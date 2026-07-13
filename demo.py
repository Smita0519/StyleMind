import json
import torch
import torch.nn as nn
from torchvision import transforms, models
from PIL import Image
import matplotlib.pyplot as plt
from tkinter import Tk, filedialog

device = "cuda" if torch.cuda.is_available() else "cpu"

with open('checkpoints/label_classes.json') as f:
    classes = json.load(f)

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

class StyleMindModel(nn.Module):
    def __init__(self, n_cat, n_tex, n_sea):
        super().__init__()
        backbone = models.mobilenet_v2(weights=None)
        self.features = backbone.features
        self.pool = nn.AdaptiveAvgPool2d(1)
        self.category_head = nn.Linear(1280, n_cat)
        self.texture_head = nn.Linear(1280, n_tex)
        self.season_head = nn.Linear(1280, n_sea)
    def forward(self, x):
        x = self.pool(self.features(x)).flatten(1)
        return self.category_head(x), self.texture_head(x), self.season_head(x)

model = StyleMindModel(len(classes['category']), len(classes['texture']), len(classes['season'])).to(device)
model.load_state_dict(torch.load('checkpoints/stylemind_full.pt', map_location=device))
model.eval()

def predict(img):
    x = transform(img).unsqueeze(0).to(device)
    with torch.no_grad():
        cat_out, tex_out, sea_out = model(x)
    cat = classes['category'][cat_out.argmax(1).item()]
    tex = classes['texture'][tex_out.argmax(1).item()]
    sea = classes['season'][sea_out.argmax(1).item()]
    cc = torch.softmax(cat_out, dim=1).max().item()
    tc = torch.softmax(tex_out, dim=1).max().item()
    sc = torch.softmax(sea_out, dim=1).max().item()
    return cat, tex, sea, cc, tc, sc

def pick_files():
    root = Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    paths = filedialog.askopenfilenames(
        title="Select clothing images",
        filetypes=[("Image files", "*.jpg *.jpeg *.png *.webp")]
    )
    root.destroy()
    return list(paths)

def show_predictions(paths):
    images = [Image.open(p).convert('RGB') for p in paths]
    n = len(images)
    fig, axes = plt.subplots(1, n, figsize=(5 * n, 6))
    if n == 1:
        axes = [axes]
    for ax, img, p in zip(axes, images, paths):
        cat, tex, sea, cc, tc, sc = predict(img)
        ax.imshow(img)
        ax.axis('off')
        ax.set_title(f"{p.split('/')[-1]}\ncat: {cat} ({cc:.2f})\ntex: {tex} ({tc:.2f})\nseason: {sea} ({sc:.2f})", fontsize=9)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    while True:
        paths = pick_files()
        if not paths:
            print("No files selected. Exiting.")
            break
        show_predictions(paths)

        choice = input("Upload more images? (y/n): ").strip().lower()
        if choice != 'y':
            print("Done.")
            break