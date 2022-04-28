import torch
from torch.utils.data import DataLoader
from torch import optim
import torch.nn as nn
from tqdm import tqdm
from Miniproject_1.others.utils import psnr


def train(train_images, val_images, net, config, writer, device='cpu'):
    batch_size = config["batch_size"]
    epochs = config["epochs"]
    checkpoint_dir = config["checkpoint_dir"]
    lr = config["learning_rate"]
    # Create PyTorch DataLoaders
    train_loader = DataLoader(train_images, shuffle=True, batch_size=batch_size)
    val_loader = DataLoader(val_images, shuffle=False, batch_size=1, drop_last=True)
    optimizer = optim.Adam(net.parameters(), lr=lr, betas=(0.9, 0.999), eps=1e-08, amsgrad=False)
    criterion = nn.MSELoss()
    global_step = 0
    max_val_score = 0
    best_val_loss = 10000
    patience = 0
    # Train
    print("Training started !\n")

    for epoch in range(epochs):
        # Train step
        net.train()
        epoch_loss = 0
        for batch in tqdm(train_loader):
            # Get image and target
            images = batch['image'].to(device=device, dtype=torch.float32)
            targets = batch['target'].to(device=device, dtype=torch.float32)
            # Forward pass
            optimizer.zero_grad()
            preds = net(images)

            xxx = preds[0].detach().cpu().numpy()
            yyy = targets[0].detach().cpu().numpy()
            # Compute loss
            loss = criterion(preds, targets)
            writer.add_scalar("Lr", optimizer.param_groups[0]['lr'], global_step)
            # Perform backward pass
            loss.backward()
            optimizer.step()
            # Update global step value and epoch loss
            global_step += 1
            epoch_loss += loss.item()
        epoch_loss = epoch_loss / len(train_loader)
        print(f'\nEpoch: {epoch} -> train_loss: {epoch_loss} \n')

        # Evaluate model after each epoch
        print(f'Validation started !\n')

        net.eval()
        # Initialize varibales
        num_val_batches = len(val_loader)
        val_score = 0
        val_loss = 0
        for i, batch in tqdm(enumerate(val_loader)):
            # Get image and gt masks
            images = batch['image'].to(device=device, dtype=torch.float32)
            targets = batch['target'].to(device=device, dtype=torch.float32)
            writer.add_image("Target", targets[0], i)

            with torch.no_grad():
                # Forward pass
                preds = net(images)
                # Add prediction to tensorboard
                writer.add_image("Prediction", preds[0].float().detach().cpu(), i)
                writer.add_image("Target", images[0].float().detach().cpu(), i)
                writer.add_image("Image", targets[0].float().detach().cpu(), i)
                # Compute validation loss
                loss = criterion(preds, targets)
                val_loss += loss.item()
                # Compute PSNR
                val_score += psnr(preds, targets)

        net.train()
        # Update validation loss
        val_loss = val_loss / len(val_loader)

        # Implement early stopping
        if val_loss > best_val_loss:
            patience += 1
        else:
            best_val_loss = val_loss
            patience = 0

        if patience == 10:
            print("Training stopped due to early stopping with patience {}.".format(patience))
            break

        print(f'\nEpoch: {epoch} -> val_loss: {val_loss}\n')
        val_score = val_score / num_val_batches

        writer.add_scalars('Loss', {'train': epoch_loss, 'val': val_loss}, global_step)

        if val_score > max_val_score:
            max_val_score = val_score
            print("Current maximum validation score is: {}\n".format(max_val_score))
            torch.save(net.state_dict(), checkpoint_dir + '/bestmodel.pth')
            print(f'Checkpoint {epoch} saved!\n')
        print('Validation PNR score is: {}\n'.format(val_score))

        writer.add_scalar("PSNR/val", val_score, global_step)