def config = [
    aws_region: "us-west-2",
    aws_secret_name: "production",
    environment: "production",
    ecs: [
      app_env: "production",
      cluster: "production",
      backend_api_service: "jlp-prod-api-ecs-service",
      backend_celery_service: "jlp-prod-celery-ecs-service",
      backend_api_task: "jlp-prod-api-ecs-task",
      backend_celery_task: "jlp-prod-celery-ecs-task"
    ],
    ecr: [
      image_name_api: "665910599311.dkr.ecr.us-west-2.amazonaws.com/jlp:production-api",
      image_name_celery: "665910599311.dkr.ecr.us-west-2.amazonaws.com/jlp:production-celery"
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
         -e DJANGO_SETTINGS_MODULE=config.settings.production \
         -e AWS_SECRET_NAME=${config.aws_secret_name} \
         -e TEMPLATE_PATH=/home/www/app/config/settings/production.template \
         -e APP_ENV=production \
         -e AWS_DEFAULT_REGION=${config.aws_region} ${config.ecr.image_name_api} \
         /bin/bash -c '/bin/bash /usr/bin/run-autotests.sh'")
      }
    }

    stage('migration') {
      if ("${RUN_MIGRATION}" == 'true') {
         sh("docker run --rm --name ${config.container}-remove_me \
         -e DJANGO_SETTINGS_MODULE=config.settings.production \
         -e AWS_SECRET_NAME=${config.aws_secret_name} \
         -e TEMPLATE_PATH=/home/www/app/config/settings/production.template \
         -e APP_ENV=production \
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

