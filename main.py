import torch
import json
import argparse


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("config_path", help="Path to config")
    arguments = parser.parse_args()
    return arguments


if __name__ == "__main__":
    args = get_args()

    with open(args.config_path) as json_config:
        config = json.load(json_config)

    noisy_imgs_1, noisy_imgs_2 = torch.load(config["train_data"])
    noisy_imgs , clean_imgs = torch.load(config["train_data"])

    print(noisy_imgs_1.shape)