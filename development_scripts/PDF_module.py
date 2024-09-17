import PyPDF2
from reportlab.pdfgen import canvas
from io import BytesIO
from typing import List, Dict
import cv2
import numpy as np
from reportlab.lib.utils import ImageReader

class Page:
    def __init__(self, template_pdf_path: str):
        """
        Initialize the Page with a PDF template.

        :param template_pdf_path: Path to the PDF template file.
        """
        # Load the template PDF
        self.template_pdf = PyPDF2.PdfReader(template_pdf_path)
        self.template_page = self.template_pdf.pages[0]

        # Get the size of the template page
        self.page_width = float(self.template_page.mediabox.width)
        self.page_height = float(self.template_page.mediabox.height)

        # Create a buffer for the overlay content
        self.packet = BytesIO()
        self.canvas = canvas.Canvas(self.packet, pagesize=(self.page_width, self.page_height))

    def get_page_size(self) -> tuple:
        """
        Get the size of the template page.

        :return: Tuple of (width, height) of the page.
        """
        return self.page_width, self.page_height
    
    def add_text(self, x: float, y: float, text: str, font: str = 'Helvetica', size: int = 12):
        """
        Add text to the page at the specified position.

        :param x: X-coordinate.
        :param y: Y-coordinate.
        :param text: Text string to add.
        :param font: Font name.
        :param size: Font size.
        """
        self.canvas.setFont(font, size)
        self.canvas.drawString(x, y, text)

    def add_image_from_cv2(self, image_cv2: np.ndarray, x: float, y: float, width: float = None, height: float = None):
        """
        Add an OpenCV image (NumPy array) to the page at the specified position.

        :param image_cv2: OpenCV image frame as a NumPy array.
        :param x: X-coordinate.
        :param y: Y-coordinate.
        :param width: Width of the image.
        :param height: Height of the image.
        """
        # Convert the OpenCV image (BGR) to PNG format in-memory
        _, buffer = cv2.imencode('.png', image_cv2)

        # Create a BytesIO object to store the PNG data
        image_stream = BytesIO(buffer.tobytes())

        # Create a reportlab ImageReader object from the in-memory PNG
        img_reader = ImageReader(image_stream)

        # Draw the image on the canvas at the specified position
        self.canvas.drawImage(img_reader, x, y, width=width, height=height)

    def get_merged_page(self) -> PyPDF2.PageObject:
        """
        Merge the overlay content with the template page and return the merged page.

        :return: Merged PDF page.
        """
        # Finalize the canvas and get the overlay PDF
        self.canvas.save()
        self.packet.seek(0)
        overlay_pdf = PyPDF2.PdfReader(self.packet)
        overlay_page = overlay_pdf.pages[0]

        # Merge the overlay page with the template page
        self.template_page.merge_page(overlay_page)
        return self.template_page

class PDF:
    def __init__(self):
        """
        Initialize the PDF object to collect pages.
        """
        self.pages: List[PyPDF2.PageObject] = []

    def add_page(self, page: Page):
        """
        Add a Page instance to the PDF.

        :param page: Page instance to add.
        """
        merged_page = page.get_merged_page()
        self.pages.append(merged_page)

    def save(self, output_pdf_path: str):
        """
        Save the collected pages into a single PDF file.

        :param output_pdf_path: Path to the output PDF file.
        """
        writer = PyPDF2.PdfWriter()
        for page in self.pages:
            writer.add_page(page)
        with open(output_pdf_path, 'wb') as f:
            writer.write(f)

# Example Usage:

pdf = PDF()
pages = []

def add_image_and_return_page(image_paths:List[str] = None, shift_info:str = None, page_no:str = None):
    page = Page(template_pdf_path = 'template.pdf')
    image_size = (180, 120)
    image_topleft_coordinates = [
        (55,640),
        (55,455),
        (55,270),
        (55,85),
        (365,640),
        (365,455),
        (365,270),
        (365,85)
    ]

    import_images = [ cv2.imread(image_path) for image_path in image_paths ]
    for i, image in enumerate(import_images):
        x, y = image_topleft_coordinates[i]
        page.add_image_from_cv2(image_cv2 = image, x=x, y=y, width=image_size[0], height=image_size[1])
        image_info = regex_file_name(image_path=image_paths[i])
        page.add_text(x=x, y=y-20, text=f"Tarih      : {image_info['date']}", font='Helvetica', size=8)
        page.add_text(x=x, y=y-30, text=f"Saat       : {image_info['time']}", font='Helvetica', size=8)
        page.add_text(x=x, y=y-40, text=f"İhlal tipi : {image_info['event_type']}", font='Helvetica', size=8)
        page.add_text(x=x, y=y-50, text=f"Konum      : {image_info['location']}", font='Helvetica', size=8)
        page.add_text(x=x, y=y-60, text=f"Ek bilgi   : {image_info['additional_info']}", font='Helvetica', size=8)
        page.add_text(x=x, y=y-70, text=f"Skor       : {image_info['float_value']}", font='Helvetica', size=8)

    return page
 
import re
def regex_file_name(image_path:str):
    filename = Path(image_path).stem 

    # Split the filename into parts
    parts = filename.split('_')

   # Extract date and time
    date = f"{parts[0]}-{parts[1]}-{parts[2]}"
    time = f"{parts[3]}:{parts[4]}:{parts[5]}"

    # Detect event type (either "restricted_area_violation" or "hardhat_violation")
    if "restricted_area_violation" in filename:
        event_type = "restricted_area_violation"
    elif "hardhat_violation" in filename:
        event_type = "hardhat_violation"
    else:
        event_type = "Unknown"

    # Extract location (handles spaces in location name)
    location_parts = filename.split(f"{event_type}_")
    location_info = location_parts[1].split('_', 1)
    location = location_info[0]

    # Extract additional info (ID and UUID)
    additional_info = location_info[1]

    # Extract the floating point number (e.g., "0n65" -> 0.65)
    match = re.search(r'_(\d+)n(\d+)_', filename)
    if match:
        float_value = float(f"{match.group(1)}.{match.group(2)}")
    else:
        float_value = None

    # Display extracted information
    print("Date:", date)
    print("Time:", time)
    print("Event Type:", event_type.replace('_', ' '))
    print("Location:", location)
    print("Additional Info:", additional_info)
    print("Floating Value:", float_value)

    return {
        "date": date,
        "time": time,
        "event_type": event_type,
        "location": location,
        "additional_info": additional_info,
        "float_value": float_value
    }

# Get image paths 
from pathlib import Path
report_images_folder = Path("/home/external_ssd/report_images")
image_paths = [ str(filepath) for filepath in report_images_folder.rglob('*') if filepath.is_file() ]

batch_size = 8
page_count = 1
for i in range(0, len(image_paths), batch_size):
    batch = image_paths[i:i + batch_size]
    print(f"Processing batch {i // batch_size + 1} with {len(batch)} images")
    if i>15:
        break
    if len(batch) == 0:
        break
    
    page = add_image_and_return_page(image_paths=batch, shift_info="shift_info", page_no=str(page_count))
    pages.append(page)
    page_count += 1
    
pdf = PDF()
for page in pages:
    pdf.add_page(page)
pdf.save('output.pdf')


# Save the PDF
# pdf.save('image_output.pdf')


# page1 = Page('template.pdf')
# page1.add_text(100, 500, "Hello World!", font='Helvetica-Bold', size=16)
# page1.add_image_from_cv2(image_cv2 = random_image, x=100, y=400, width=200, height=100)

# # Create second page with a different template
# page2 = Page('template.pdf')
# page2.add_text(50, 700, "Second Page", font='Times-Roman', size=14)
# page2.add_image_from_cv2(image_cv2 = random_image, x=50, y=600, width=150, height=150)

# # Combine pages into a single PDF
# pdf = PDF()
# pdf.add_page(page1)
# pdf.add_page(page2)
# pdf.save('combined_output.pdf')

# from pathlib import Path
# ssd_path = Path("/home/external_ssd")

# # List all files in the SSD path
# for filepath in ssd_path.rglob('*'):
#     if filepath.is_file():
#         print(filepath)



