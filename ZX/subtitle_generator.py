from PIL import Image, ImageDraw, ImageFont
import os

class SubtitleGenerator:
    def __init__(self, font_path, base_image_path):
        """
        初始化字幕生成器
        :param font_path: 字体文件路径
        :param base_image_path: 基础图片路径
        """
        self.font_path = font_path
        self.base_image_path = base_image_path
        self._check_files()

    def _check_files(self):
        """检查字体文件和图片文件是否存在"""
        if not os.path.exists(self.font_path):
            raise FileNotFoundError(f"字体文件未找到: {self.font_path}")
        if not os.path.exists(self.base_image_path):
            raise FileNotFoundError(f"基础图片未找到: {self.base_image_path}")

    def generate_subtitle_image(self, text, font_size=40, x_pos=None, y_pos=None, padding=50, text_color=(255, 255, 255)):
        """
        生成带字幕的图片
        :param text: 字幕文本
        :param font_size: 字体大小
        :param x_pos: 文字 X 坐标（None 则居中）
        :param y_pos: 文字 Y 坐标（None 则底部）
        :param padding: 文字与边缘的间距
        :param text_color: 文字颜色，RGB元组
        :return: 处理后的图片对象
        """
        # 加载图片和字体
        image = Image.open(self.base_image_path)
        font = ImageFont.truetype(self.font_path, font_size)

        # 创建绘图对象
        draw = ImageDraw.Draw(image)

        # 获取文本尺寸
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]

        # 计算图片需要的最小宽度
        required_width = text_width + (padding * 2)

        # 如果文本宽度超过图片宽度，调整图片大小
        if required_width > image.width:
            scale_factor = required_width / image.width
            new_size = (int(image.width * scale_factor), int(image.height * scale_factor))
            image = image.resize(new_size, Image.Resampling.LANCZOS)
            draw = ImageDraw.Draw(image)

        # 计算文字位置
        if x_pos is None:
            # 使用文本宽度的一半来确保中心对齐
            x = (image.width - text_width) // 2
        else:
            # 从指定位置减去文本宽度的一半来实现中心对齐
            x = x_pos - (text_width // 2)

        if y_pos is None:
            # 底部对齐，使用文本高度确保文字不会超出边界
            y = image.height - text_height - padding
        else:
            # 从指定位置减去文本高度来实现底部对齐
            y = y_pos - text_height

        # 绘制文字
        draw.text((x, y), text, font=font, fill=text_color)

        return image

    def process_subtitle_file(self, subtitle_file, output_dir, **kwargs):
        """
        处理字幕文件并生成对应的图片
        :param subtitle_file: 字幕文件路径
        :param output_dir: 输出目录
        :param kwargs: 传递给generate_subtitle_image的参数
        """
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        with open(subtitle_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        for i, line in enumerate(lines):
            line = line.strip()
            if line:  # 跳过空行
                image = self.generate_subtitle_image(line, **kwargs)
                output_path = os.path.join(output_dir, f'subtitle_{i+1:03d}.png')
                image.save(output_path)

# 使用示例
def main():
    # 设置路径
    font_path = 'AlimamaFangYuanTiVF-Thin.ttf'
    base_image_path = 'asd_00000.png'
    subtitle_file = '新建文本文档.txt'
    output_dir = r'C:\Users\Administrator\Desktop\摘星0_0_1\ZX\新建文件夹'

    try:
        # 获取基础图片尺寸
        base_image = Image.open(base_image_path)
        image_width = base_image.width
        base_image.close()

        # 创建字幕生成器实例
        generator = SubtitleGenerator(font_path, base_image_path)

        # 处理字幕文件
        generator.process_subtitle_file(
            subtitle_file,
            output_dir,
            font_size=40,
            x_pos=image_width // 2,  # 使用基础图片宽度的一半作为中心点
            y_pos=930,
            padding=50,
            text_color=(255, 255, 255)
        )
        print(f'字幕图片已生成到目录: {output_dir}')

    except Exception as e:
        print(f'发生错误: {str(e)}')

if __name__ == '__main__':
    main()