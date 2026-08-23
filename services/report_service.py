from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer
)

from reportlab.lib.styles import (
    getSampleStyleSheet
)

def generate_pdf(
        title,
        text,
        filename
):

    doc = SimpleDocTemplate(filename)

    styles = getSampleStyleSheet()

    elements = [
        Paragraph(title, styles['Title']),
        Spacer(1, 12),
        Paragraph(text, styles['BodyText'])
    ]

    doc.build(elements)
