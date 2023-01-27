// def config = [
//   project: 'backend',
//   environment: 'development',
//   namespace: 'jlp',
//   dev_environment: 'True',
//   docker_file: 'ci/docker/Dockerfile',
//   image: 'registry.saritasa.com/jlp/backend:develop'
// ]

// node ('docker') {
//   try {
//     stage('clean') {
//       if ("${BUILD_CLEAN}" == "true") {
//         gitlabCommitStatus('clean') {
//           cleanWs()
//         }
//       }
//     }
//     stage('scm') {
//       gitlabCommitStatus('scm') {
//         checkout(scm)
//       }
//     }
//     stage('build') {
//       gitlabCommitStatus('build') {
//         sh("docker build \
//         --file ci/docker/Dockerfile \
//         --no-cache=${BUILD_CLEAN} \
//         --build-arg APP_ENV=${config.environment} \
//         --build-arg DEV_ENVIRONMENT=${config.dev_environment} \
//         --rm --tag ${config.image} .")
//       }
//     }
//     stage('registry') {
//       gitlabCommitStatus('registry') {
//         withCredentials([usernamePassword(credentialsId: 'jenkins-gitlab-token', passwordVariable: 'PASSWORD', usernameVariable: 'USERNAME')]) {
//           sh("docker login --username ${env.USERNAME} --password ${env.PASSWORD} registry.saritasa.com")
//           sh("docker push ${config.image}")
//         }
//       }
//     }
//     stage('autotests') {
//       if ("${AUTOTEST}" == "true") {
//         gitlabCommitStatus('autotests') {
//           withKubeConfig(credentialsId: 'saritasa-k8s-develop-token', serverUrl: "${K8S_DEVELOPMENT_URL}") {
//             sh("kubectl delete -n ${config.namespace} -f ci/chart/${config.environment}/autotests.yaml || true")
//             sh("kubectl create -f ci/chart/${config.environment}/autotests.yaml")

//             endTimer = System.currentTimeMillis() + 600000;
//             while(true) {
//               sleep(10)
//               jobStatus = sh(returnStdout: true,
//               script:"kubectl -n ${config.namespace} get pods \
//               --selector=job-name=autotests \
//               '-o=jsonpath={.items..status.containerStatuses..state.terminated.reason}'").trim()

//               switch(jobStatus) {
//                 case 'Completed':
//                   println('autotests completed')
//                   return;
//                 case '':
//                   println('waiting for autotests status...')
//                   break;
//                 default:
//                   errorMessage = sh(returnStdout: true,script: "kubectl -n ${config.namespace} logs jobs/autotests").trim()
//                   error(errorMessage)
//                   break;
//               }

//               if(System.currentTimeMillis() > endTimer) {
//                 error('autotests failed by timeout')
//                 return;
//               }
//             }
//           }
//         }
//       }
//     }
//     stage('migrations') {
//       gitlabCommitStatus('migrations') {
//         withKubeConfig(credentialsId: 'saritasa-k8s-develop-token', serverUrl: "${K8S_DEVELOPMENT_URL}") {
//           sh(
//             "kubectl delete -n ${config.namespace} -f ci/chart/${config.environment}/migrations.yaml || true && \
//              kubectl create -f ci/chart/${config.environment}/migrations.yaml && \
//              kubectl -n ${config.namespace} wait --for=condition=complete --timeout=90s job/migrations \
//              ")
//         }
//       }
//     }
//     stage('deploy') {
//       gitlabCommitStatus('deploy') {
//         withKubeConfig(credentialsId: 'saritasa-k8s-develop-token', serverUrl: "${K8S_DEVELOPMENT_URL}") {
//           sh(
//             "helm --namespace ${config.namespace} \
//             upgrade --cleanup-on-fail --install ${config.project} \
//             ci/chart/${config.environment} \
//             ")
//         }
//       }
//     }
//   } catch (error) {
//     currentBuild.result = 'FAILURE'
//     println("ERROR: $error")
//     emailext(
//       subject: "Build - ${currentBuild.currentResult}: ${JOB_NAME}: ${BUILD_NUMBER}",
//       body: "\
//       <h1 style='text-align:center;color:#ecf0f1;background-color:#ff5252;border-color:#ff5252'> \
//         ${currentBuild.currentResult} \
//       </h1> \
//       <b>Job url</b>: ${BUILD_URL}<br> \
//       <code>$error</code>",
//       recipientProviders: [requestor(), developers(), brokenBuildSuspects(), brokenTestsSuspects()]
//     )
//   }
// }

def config = [
    aws_region: "us-east-1",
    aws_secret_name: "development",
    environment: "development",
    ecs: [
      app_env: "development",
      cluster: "development",
      backend_api_service: "juslaw-development-ApiService",
      backend_celery_service: "juslaw-development-CeleryService",
      backend_api_task: "juslaw-development-api-ApiTask",
      backend_celery_task: "juslaw-development-CeleryTask"
    ],
    ecr: [
      image_name_api: "665910599311.dkr.ecr.us-west-2.amazonaws.com/jlp:development-api",
      image_name_celery: "665910599311.dkr.ecr.us-west-2.amazonaws.com/jlp:development-celery"
    ]
 ]

node {
  try {
    stage('clean-up') {
      if ("${BUILD_CLEAN}" == "true") {
        cleanWs()
      }
    }

    stage('scm') {
      checkout(scm)
    }

    stage('build:api') {
        sh("docker build -f ci/docker/Dockerfile --no-cache=${BUILD_CLEAN} \
        --build-arg APP_ENV=${config.environment} \
        --build-arg AWS_REGION=${config.aws_region} \
        --rm --tag ${config.ecr.image_name_api} .")
    }

    stage('build:celery') {
        sh("docker build -f ci/docker/Dockerfile --no-cache=${BUILD_CLEAN} \
        --build-arg APP_ENV=${config.environment} \
        --build-arg AWS_REGION=${config.aws_region} \
        --rm --tag ${config.ecr.image_name_celery} .")
    }

    stage('autotests') {
      if ("${RUN_TESTS}" == 'true') {
         sh("docker run --rm --name remove_me \
         -e DJANGO_SETTINGS_MODULE=config.settings.development \
         -e AWS_SECRET_NAME=${config.aws_secret_name} \
         -e TEMPLATE_PATH=/home/www/app/config/settings/development.template \
         -e APP_ENV=development \
         -e AWS_DEFAULT_REGION=${config.aws_region} ${config.ecr.image_name_api} \
         /bin/bash -c '/bin/bash /usr/bin/run-autotests.sh'")
      }
    }

    stage('migration') {
      if ("${RUN_MIGRATION}" == 'true') {
         sh("docker run --rm --name ${config.container}-remove_me \
         -e DJANGO_SETTINGS_MODULE=config.settings.development \
         -e AWS_SECRET_NAME=${config.aws_secret_name} \
         -e TEMPLATE_PATH=/home/www/app/config/settings/development.template \
         -e APP_ENV=development \
         -e AWS_DEFAULT_REGION=${config.aws_region} ${config.ecr.image_name_api} \
         /bin/bash -c '/bin/bash /usr/bin/run-migrations.sh'")
      }
    }

  stage('ecr') {
    sh(script: sh(script: "aws ecr get-login --region ${config.aws_region} --no-include-email", returnStdout: true))
    sh(script: "docker push ${config.ecr.image_name_api}")
    sh(script: "docker push ${config.ecr.image_name_celery}")
  }

  stage('ecs-backend') {
    withEnv(["AWS_DEFAULT_REGION=${config.aws_region}"]) {
      sh(script: "aws ecs update-service --force-new-deployment --cluster ${config.ecs.cluster} --service ${config.ecs.backend_api_service} --task-definition ${config.ecs.backend_api_task}")
      sh(script: "aws ecs update-service --force-new-deployment --cluster ${config.ecs.cluster} --service ${config.ecs.backend_celery_service} --task-definition ${config.ecs.backend_celery_task}")
    }
  }

    stage('clean') {
        sh("docker rm remove_me --force || true")
    }

  }
  catch (error) {
    println("ERROR: $error")
    currentBuild.result = 'FAILURE'
    emailext subject: 'Job jlp-backend failure', body: '$BUILD_URL Job jlp-backend failure', recipientProviders: [requestor()]
  }
}

