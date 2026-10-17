from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

def create_pdf(filename):
    pdf = SimpleDocTemplate(filename)
    styles = getSampleStyleSheet()
    story = []
    story.append(Paragraph("This is a sample PDF file.", styles['Normal']))
    story.append(Paragraph("Created for testing with LangChain.", styles['Normal']))
    pdf.build(story)

if __name__ == "__main__":
    create_pdf("sample.pdf")
    print("sample.pdf created successfully!")
