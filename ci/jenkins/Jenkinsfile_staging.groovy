def config = [
  project: 'backend',
  environment: 'staging',
  namespace: 'jlp-staging',
  dev_environment: 'True',
  docker_file: 'ci/docker/Dockerfile',
  image: 'registry.saritasa.com/jlp/backend:staging'
]

node ('docker') {
  try {
    stage('clean') {
      if ("${BUILD_CLEAN}" == "true") {
        gitlabCommitStatus('clean') {
          cleanWs()
        }
      }
    }
    stage('scm') {
      gitlabCommitStatus('scm') {
        checkout(scm)
      }
    }
    stage('build') {
      gitlabCommitStatus('build') {
        sh("docker build \
        --file ${config.docker_file} \
        --no-cache=${BUILD_CLEAN} \
        --build-arg APP_ENV=${config.environment} \
        --build-arg DEV_ENVIRONMENT=${config.dev_environment} \
        --rm --tag ${config.image} .")
      }
    }
    stage('registry') {
      gitlabCommitStatus('registry') {
        withCredentials([usernamePassword(credentialsId: 'jenkins-gitlab-token', passwordVariable: 'PASSWORD', usernameVariable: 'USERNAME')]) {
          sh("docker login --username ${env.USERNAME} --password ${env.PASSWORD} registry.saritasa.com")
          sh("docker push ${config.image}")
        }
      }
    }
    stage('autotests') {
      if ("${AUTOTEST}" == "true") {
        gitlabCommitStatus('autotests') {
          withKubeConfig(credentialsId: 'saritasa-k8s-develop-token', serverUrl: "${K8S_DEVELOPMENT_URL}") {
            sh("kubectl delete -n ${config.namespace} -f ci/chart/${config.environment}/autotests.yaml || true")
            sh("kubectl create -f ci/chart/${config.environment}/autotests.yaml")

            endTimer = System.currentTimeMillis() + 600000;
            while(true) {
              sleep(10)
              jobStatus = sh(returnStdout: true,
              script:"kubectl -n ${config.namespace} get pods \
              --selector=job-name=autotests \
              '-o=jsonpath={.items..status.containerStatuses..state.terminated.reason}'").trim()

              switch(jobStatus) {
                case 'Completed':
                  println('autotests completed')
                  return;
                case '':
                  println('waiting for autotests status...')
                  break;
                default:
                  errorMessage = sh(returnStdout: true,script: "kubectl -n ${config.namespace} logs jobs/autotests").trim()
                  error(errorMessage)
                  break;
              }

              if(System.currentTimeMillis() > endTimer) {
                error('autotests failed by timeout')
                return;
              }
            }
          }
        }
      }
    }
    stage('migrations') {
      gitlabCommitStatus('migrations') {
        withKubeConfig(credentialsId: 'saritasa-k8s-develop-token', serverUrl: "${K8S_DEVELOPMENT_URL}") {
          sh(
            "kubectl delete -n ${config.namespace} -f ci/chart/${config.environment}/migrations.yaml || true &&\
             kubectl create -f ci/chart/${config.environment}/migrations.yaml &&\
             kubectl -n ${config.namespace} wait --for=condition=complete --timeout=90s job/migrations \
            ")
        }
      }
    }
    stage('deploy') {
      gitlabCommitStatus('deploy') {
        withKubeConfig(credentialsId: 'saritasa-k8s-develop-token', serverUrl: "${K8S_DEVELOPMENT_URL}") {
          sh(
            "helm --namespace ${config.namespace} \
            upgrade --cleanup-on-fail --install ${config.project} \
            ci/chart/${config.environment} \
            ")
        }
      }
    }
  } catch (error) {
    currentBuild.result = 'FAILURE'
    println("ERROR: $error")
    emailext(
      subject: "Build - ${currentBuild.currentResult}: ${JOB_NAME}: ${BUILD_NUMBER}",
      body: "\
      <h1 style='text-align:center;color:#ecf0f1;background-color:#ff5252;border-color:#ff5252'> \
        ${currentBuild.currentResult} \
      </h1> \
      <b>Job url</b>: ${BUILD_URL}<br> \
      <code>$error</code>",
      recipientProviders: [requestor(), developers(), brokenBuildSuspects(), brokenTestsSuspects()]
    )
  }
}
