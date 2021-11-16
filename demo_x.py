import argparse
import os
from PIL import Image
import time
import torch
from torchvision import transforms
import sys
sys.path.append("models")
os.environ['CUDA_VISIBLE_DEVICES'] = '0'
import csv
import numpy as np
from models import models
from train_x import batched_predict
from utils import calc_psnr, ssim



if __name__ == '__main__':
    torch.cuda.empty_cache()
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', default='save/WHURS19_edsrblx2/epoch-best.pth')
    parser.add_argument('--lrdir', default=r'/home/ww020823/yxc/dataset/WHU-RS19-test/LR/x4')
    parser.add_argument('--hrdir', default=r'/home/ww020823/yxc/dataset/WHU-RS19-test/GT')
    args = parser.parse_args()

    model = models.make(torch.load(args.model)['model'], load_sd=True).cuda()

    scale = 4
    lr_dir = args.lrdir
    hr_dir = args.hrdir
    sr_dir = os.path.join('testimg', args.model.split('/')[1])
    #sr_dir = r"testimg/WHURS19_test_high_edsrblx2"
    if not os.path.exists(sr_dir):
        os.makedirs(sr_dir)
    result_csv = os.path.join(sr_dir, args.model.split('/')[1]+".csv")

    psnr_cnt = []
    ssim_cnt = []

    with open(result_csv, "w+", newline='') as f:
        writer = csv.writer(f)
        for name in os.listdir(hr_dir):
            #lr_path = os.path.join(lr_dir, name)
            #lr_img = Image.open(lr_path)
            hr_path = os.path.join(hr_dir, name)
            hr_img = Image.open(hr_path).convert('RGB')
            img = transforms.Resize((int(hr_img.height/scale), int(hr_img.width/scale)), Image.BICUBIC)(hr_img)
            #img.save(lr_path)
            img = transforms.ToTensor()(img)
            bimg = ((img - 0.5) / 0.5).cuda().unsqueeze(0)

            pred = batched_predict(model, bimg)
            pred = (pred * 0.5 + 0.5).clamp(0, 1)

            hr = transforms.ToTensor()(hr_img).cuda().unsqueeze(0)

            psnr_v = calc_psnr(pred, hr).item()
            ssim_v = ssim(pred, hr).item()
            psnr_cnt.append(psnr_v)
            ssim_cnt.append(ssim_v)

            transforms.ToPILImage()(pred[0].cpu()).save(os.path.join(sr_dir, name).replace('jpg', 'png'))
            #print(name, psnr_v, ssim_v)
            writer.writerow([name, psnr_v, ssim_v])
        print(np.mean(psnr_cnt))
        print(np.mean(ssim_cnt))


