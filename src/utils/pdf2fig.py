import math
from pdf2image import convert_from_path
from PIL import Image, ImageDraw

def create_pdf_summary(pdf_path, output_path, thumb_width=300, padding=10):
    """
    Generate a summary image of a PDF file in 16:9 aspect ratio.
    """
    print(f"Loading PDF: {pdf_path} ...")
    
    try:
        pages = convert_from_path(pdf_path, dpi=100)
    except Exception as e:
        print(f"Error: Failed to read PDF (please check if Poppler is installed). \nDetails: {e}")
        return

    total_pages = len(pages)
    if total_pages == 0:
        print("PDF is empty.")
        return

    first_page = pages[0]
    w, h = first_page.size
    thumb_height = int(thumb_width * (h / w))


    target_ratio = 16 / 9
    page_ratio = h / w 
    
    calc_cols = math.sqrt(total_pages * page_ratio * target_ratio)
    cols = int(round(calc_cols))
    cols = max(1, min(cols, total_pages))
    rows = math.ceil(total_pages / cols)

    print(f"Total {total_pages} pages.")
    print(f"Layout strategy: {cols} columns x {rows} rows (targeting 16:9)")

    canvas_width = cols * thumb_width + (cols + 1) * padding
    canvas_height = rows * thumb_height + (rows + 1) * padding
    
    bg_color = (240, 240, 240) 
    canvas = Image.new('RGB', (canvas_width, canvas_height), bg_color)

    draw = ImageDraw.Draw(canvas)

    for i, page in enumerate(pages):
        page.thumbnail((thumb_width, thumb_height), Image.Resampling.LANCZOS)
        
        row_idx = i // cols
        col_idx = i % cols
        
        x = padding + col_idx * (thumb_width + padding)
        y = padding + row_idx * (thumb_height + padding)
        
        canvas.paste(page, (x, y))
        draw.rectangle([x, y, x + thumb_width, y + thumb_height], outline="black", width=1)
        
    canvas.save(output_path)
    print(f"Processing completed! Image saved to: {output_path}")
    print(f"Final image size: {canvas_width}x{canvas_height} (ratio: {canvas_width/canvas_height:.2f})")

if __name__ == "__main__":
    input_pdf = "智能共生·价值增长：跨越初步探索期的金融智能体.pdf" 
    output_img = "智能共生·价值增长：跨越初步探索期的金融智能体_preview.jpg"
    
    create_pdf_summary(input_pdf, output_img)