import os
from base64 import b64decode
from subprocess import PIPE, run

from aiofauna.utils import setup_logging
from aiohttp import ClientSession
from boto3 import Session
from docker import from_env
from pydantic import BaseConfig, BaseModel, BaseSettings, Field
from urllib3 import response


class Env(BaseSettings):
    AWS_ACCESS_KEY_ID:str = Field(..., env='AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY:str = Field(...,env='AWS_SECRET_ACCESS_KEY')
    AWS_DEFAULT_REGION:str = Field(...,env='AWS_DEFAULT_REGION')
    AWS_LAMBDA_ROLE:str = Field(...,env='AWS_LAMBDA_ROLE')
    AWS_ECR_URL:str = Field(...,env='AWS_ECR_URL')
    DOCKER_URL:str = Field(...,env='DOCKER_URL')
    
    class Config(BaseConfig):
        env_file: str = '.env'
        env_file_encoding = 'utf-8'
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
    
env = Env()
logger = setup_logging(__name__)
docker = from_env()
aws = Session(
    aws_access_key_id=env.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=env.AWS_SECRET_ACCESS_KEY,
    region_name=env.AWS_DEFAULT_REGION
)

ecr = aws.client('ecr')
ecs = aws.client('ecs')


def login_ecr():
    logger.info('Logging in to ECR')
    response = ecr.get_authorization_token()
    token = response['authorizationData'][0]['authorizationToken']
    username, password = b64decode(token).decode().split(':')
    ecr_url = env.AWS_ECR_URL
    logger.info('Logging in to ECR')
    docker.login(username, password, registry=ecr_url)
    logger.info('Logged in to ECR')
    return ecr_url


def build_image(path:str,name:str, tag:str='latest'):
    logger.info(f'Building image {name}:{tag}')
    response = docker.images.build(path=path, tag=f'{name}:{tag}')
    assert isinstance(response, tuple)
    image, logs = response
    for line in logs:
        logger.debug(line)
    logger.info(f'Image {name}:{tag} built')
    
def push_image(name:str, tag:str='latest'):
    logger.info(f'Pushing image {name}:{tag}')
    ecr_url = login_ecr()
    image = f'{name}:{tag}'
    response = docker.images.push(ecr_url, image)
    assert isinstance(response, response.HTTPResponse)
    for line in response:
        logger.debug(line)
    logger.info(f'Image {name}:{tag} pushed')
 
 
def main():
    name = input('Enter image name: ')
    tag = input('Enter image tag: ')
    path = input('Enter path to Dockerfile: ')
    build_image(path, name, tag)
    push_image(name, tag)
    logger.info('Done')

main()