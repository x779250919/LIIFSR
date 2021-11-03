import argparse
import os
import yaml
import math
import torch
from torch.utils.data import DataLoader
from torchvision.utils import save_image
from tqdm import tqdm

import sys
sys.path.append("models")
import datasets
import models
import utils
from train_L0 import batched_predict, eval


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config')
    parser.add_argument('--model')
    parser.add_argument('--gpu', default='0')
    parser.add_argument('--save_sr', default=False)

    args = parser.parse_args()

    os.environ['CUDA_VISIBLE_DEVICES'] = args.gpu

    with open(args.config, 'r') as f:
        config = yaml.load(f, Loader=yaml.FullLoader)

    spec = config['test_dataset']
    dataset = datasets.make(spec['dataset'])
    dataset = datasets.make(spec['wrapper'], args={'dataset': dataset})
    loader = DataLoader(dataset, batch_size=spec['batch_size'], num_workers=0, pin_memory=True)

    sv_file = torch.load(args.model)
    print(f'epoch——{sv_file["epoch"]}')

    model_spec = torch.load(args.model)['model']
    model = models.make(model_spec, load_sd=True).cuda()

    psnr,ssim = eval(loader, model, data_norm=config.get('data_norm'), verbose=True)
    print(f'result: psnr={psnr:.4f} ssim={ssim:.4f}')
