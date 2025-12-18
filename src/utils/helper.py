import base64
import re

def image_to_base64(image_path: str) -> str:
    """Converts an image file to a base64 encoded string."""
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode()
    except Exception as e:
        return ""

def extract_markdown(text: str) -> str:
    """Extract Markdown content enclosed in code blocks."""
    pattern = r"```markdown\s*(.*?)\s*```"
    matches = re.findall(pattern, text, re.DOTALL)
    if matches:
        return matches[0].strip()
    return text


def get_md_img(img_path: str, img_name: str, idx: int):
    # Append data-source info when encoded within the filename
    if "_" in img_name:
        prefixs = img_name.split("_")
        title = prefixs[0]
        sources = ",".join(prefixs[1:])
        img_name = f'{title} (Data source: {sources})'
    return f"""\n\n![Chart {idx}: {img_name}]({img_path})\n\n"""