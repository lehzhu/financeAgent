
import sys
from bs4 import BeautifulSoup
import warnings
from bs4 import XMLParsedAsHTMLWarning

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

# Get the file path from the command-line arguments
file_path = sys.argv[1]

# Read the HTML content from the file
with open(file_path, 'r', encoding='utf-8') as f:
    html_content = f.read()

# Parse the HTML using BeautifulSoup
soup = BeautifulSoup(html_content, 'lxml')

# Find and remove the hidden XBRL header
for hidden_tag in soup.find_all('ix:hidden'):
    hidden_tag.decompose()

# Extract the text content from the rest of the document
text_content = soup.body.get_text(separator='\n', strip=True)

# Print the text content to standard output
print(text_content)

