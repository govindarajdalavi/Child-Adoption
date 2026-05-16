import sys
from PIL import Image

def remove_white_background(image_path, output_path, threshold=220):
    img = Image.open(image_path).convert("RGBA")
    datas = img.getdata()

    newData = []
    for item in datas:
        r, g, b, a = item
        intensity = (r + g + b) / 3
        
        if intensity > threshold:
            # Map intensity to alpha
            # 255 -> 0 alpha
            # threshold -> 255 alpha
            alpha = int(255 * (255 - intensity) / (255 - threshold))
            # Also slightly darken the edge to prevent white halo
            newData.append((r, g, b, alpha))
        else:
            newData.append(item)

    img.putdata(newData)
    img.save(output_path, "PNG")
    print(f"Saved {output_path}")

if __name__ == "__main__":
    remove_white_background('static/images/child.png', 'static/images/child.png')
