from PIL import Image, ImageDraw, ImageFont
import os

class SubtitleProcessor:
    def __init__(self, font_path="msyh.ttc", font_size=40, text_color=(255, 255, 255)):
        self.font_path = r"C:/Windows/Fonts/阿里妈妈方圆体vf"
        self.font_size = 5
        self.text_color = (255, 255, 255)
        self.font = ImageFont.truetype(self.font_path, self.font_size)

    def process_image(self, image_path, text, position_y=None):
        # 打开原始图片
        img = Image.open(image_path)
        
        # 获取文字大小
        draw = ImageDraw.Draw(img)
        text_width, text_height = draw.textsize(text, font=self.font)
        
        # 如果图片宽度小于文字宽度，调整图片大小
        if img.width < text_width + 40:  # 添加40像素的边距
            new_width = text_width + 40
            ratio = new_width / img.width
            new_height = int(img.height * ratio)
            img = img.resize((new_width, new_height), Image.LANCZOS)
        
        # 重新创建Draw对象
        draw = ImageDraw.Draw(img)
        
        # 计算文字位置
        x = (img.width - text_width) // 2  # 水平居中
        if position_y is None:
            y = img.height - text_height - 20  # 默认底部位置
        else:
            y = position_y
        
        # 绘制文字
        draw.text((x, y), text, font=self.font, fill=self.text_color)
        
        return img

    def process_subtitle_file(self, image_path, subtitle_file, output_dir):
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        # 读取字幕文件
        with open(subtitle_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 处理每一行字幕
        for i, line in enumerate(lines):
            text = line.strip()
            if text:  # 跳过空行
                output_path = os.path.join(output_dir, f'output_{i+1}.png')
                img = self.process_image(image_path, text)
                img.save(output_path)

def main():
    # 使用示例
    processor = SubtitleProcessor(
        font_path=r"C:/Windows/Fonts/阿里妈妈方圆体vf",  # 微软雅黑字体路径
        font_size=10,
        text_color=(255, 255, 255)  # 白色文字
    )
    
    # 处理单张图片
    img = processor.process_image(
        "C:\Users\Administrator\Desktop\新建文件夹 (2)\第三版-在长沙都实现-唱词.png"
        "这是测试文字",
        position_y=500  # 可选：指定垂直位置
    )
    img.save("output.png")
    
    # 处理整个字幕文件
    processor.process_subtitle_file(
        "input.png",
        "subtitles.txt",
        "output_folder"
    )

if __name__ == "__main__":
    main()