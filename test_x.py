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


def batched_predict(model, inp):
    model.eval()
    with torch.no_grad():
        pred = model(inp)
    return pred


def eval(loader, model, data_norm=None, verbose=False):
    model.eval()
    if data_norm is None:
        data_norm = {
            'inp': {'sub': [0], 'div': [1]},
            'gt': {'sub': [0], 'div': [1]}
        }

    t = data_norm['inp']
    inp_sub = torch.FloatTensor(t['sub']).view(1, -1, 1, 1).cuda()
    inp_div = torch.FloatTensor(t['div']).view(1, -1, 1, 1).cuda()
    t = data_norm['gt']
    gt_sub = torch.FloatTensor(t['sub']).view(1, 1, -1).cuda()
    gt_div = torch.FloatTensor(t['div']).view(1, 1, -1).cuda()

    max_psnr = 0
    max_ssim = 0

    val_psnr = utils.Averager()
    val_ssim = utils.Averager()

    pbar = tqdm(loader, leave=False, desc='val')
    for batch in pbar:
        for k, v in batch.items():
            batch[k] = v.cuda()
        inp = (batch['inp'] - inp_sub) / inp_div


        pred = batched_predict(model,inp)
        pred = (pred * gt_div + gt_sub).clamp_(0, 1)

        psnr = utils.calc_psnr(pred, batch['gt'])
        val_psnr.add(psnr.item(), inp.shape[0])

        ssim = utils.ssim(pred, batch['gt'])
        val_ssim.add(ssim.item(), inp.shape[0])

        if psnr > max_psnr:
            max_psnr = psnr
            #save_image(pred, f"testimg/max_psnr.jpg", nrow=int(math.sqrt(pred.shape[0])))
        if ssim > max_ssim:
            max_ssim = ssim
            #save_image(pred, f"testimg/max_ssim.jpg", nrow=int(math.sqrt(pred.shape[0])))

        if verbose:
            pbar.set_description(f'PSNR {val_psnr.item():.4f} SSIM {val_ssim.item():.4f}')

    return val_psnr.item(), val_ssim.item()



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
    model_spec = torch.load(args.model)['model']
    model = models.make(model_spec, load_sd=True).cuda()

    psnr,ssim = eval(loader, model, data_norm=config.get('data_norm'), verbose=True)
    print(f'result: psnr={psnr:.10f} ssim={ssim:.10f}')
