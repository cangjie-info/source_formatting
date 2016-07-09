import re
from bs4 import BeautifulSoup 

output_file = open('mz_extraction1.txt', 'w')
output_file.write('@@container\n')

def main():
    for file_number in range(1, 15):
        output_file.write("@@subcontainer\n".format(file_number))
        soup = BeautifulSoup(open("mz{}.html".format(file_number)))
        process(soup)

def process(soup):
    content3 = soup.find("div", id="content3")
    table_border0 = content3.find("table", border="0")
    text_list = table_border0.find_all("td", class_=re.compile("[ctext|etext]"))
    for text in text_list:
        string_contents = ''
        for stuff in text.stripped_strings:
            string_contents += stuff
        if string_contents == '':
            continue
        if 'opt' in text['class'] and 'ctext' in text['class']:
            output_file.write("@@narrative\n")
        elif 'opt' in text['class']:
            pass
        else:
            if 'ctext' in text['class']:
                output_file.write('@@text\n')
            elif 'etext' in text['class']:
                output_file.write('@@translation_unit\n')
            output_file.write(string_contents + '\n')

if __name__ == "__main__":
    main()
