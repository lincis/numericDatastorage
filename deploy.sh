#!/bin/bash
chmod 600 deploy_rsa
ssh -o StrictHostKeyChecking=no -i deploy_rsa $DEPLOY_HOST "~/deploy-nds.sh"
