import os

def convert_seg_to_det(input_dir, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    txt_files = [f for f in os.listdir(input_dir) if f.endswith(".txt")]

    for txt_file in txt_files:
        input_path = os.path.join(input_dir, txt_file)
        output_path = os.path.join(output_dir, txt_file)

        with open(input_path, "r") as f:
            lines = f.readlines()

        det_lines = []
        for line in lines:
            data = list(map(float, line.strip().split()))
            if len(data) < 6:
                continue  # 跳过异常行
            cls = int(data[0])
            coords = data[1:]
            xs = coords[0::2]
            ys = coords[1::2]
            xmin, xmax = min(xs), max(xs)
            ymin, ymax = min(ys), max(ys)
            cx = (xmin + xmax) / 2
            cy = (ymin + ymax) / 2
            w = xmax - xmin
            h = ymax - ymin
            det_lines.append(f"{cls} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}\n")

        with open(output_path, "w") as f:
            f.writelines(det_lines)

        print(f"✅ {txt_file} 转换完成，共 {len(det_lines)} 个目标")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Convert YOLOv8-Seg labels to YOLOv8-Det labels")
    parser.add_argument("--input_dir", required=True, help="原始分割标签路径")
    parser.add_argument("--output_dir", required=True, help="输出检测标签路径")
    args = parser.parse_args()

    convert_seg_to_det(args.input_dir, args.output_dir)
