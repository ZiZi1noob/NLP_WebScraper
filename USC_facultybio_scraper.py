from bs4 import BeautifulSoup
from selenium import webdriver 
from selenium.webdriver.chrome.options import Options
import re 
import urllib
import pandas as pd


#create a webdriver object and set options for headless browsing
options = Options()
options.headless = True
# go to https://chromedriver.chromium.org/downloads for downloading the newest version. 
driver = webdriver.Chrome('C:/Users/ZiZi/OneDrive - University of Illinois - Urbana/CS410 Text Information Sytem/MP2.1-WebScraper/scraper_code/chromedriver',options=options)

#uses webdriver object to execute javascript code and get dynamically loaded webcontent
def get_js_soup(url,driver):
    driver.get(url)
    res_html = driver.execute_script('return document.body.innerHTML')
    soup = BeautifulSoup(res_html,'html.parser') #beautiful soup object to be used for parsing html content
    return soup

#tidies extracted text 
def process_bio(bio):
    bio = bio.encode('ascii',errors='ignore').decode('utf-8')       #removes non-ascii characters
    bio = re.sub('\s+',' ',bio)       #repalces repeated whitespace characters with single space
    return bio
'''
More tidying
Sometimes the text extracted HTML webpage may contain javascript code and some style elements. 
This function removes script and style tags from HTML so that extracted text does not contain them.
'''
def remove_script(soup):
    for script in soup(["script", "style"]):
        script.decompose()
    return soup


#Checks if bio_url is a valid faculty homepage
def is_valid_homepage(bio_url,dir_url):
    if bio_url.endswith('.pdf'): #we're not parsing pdfs
        return False
    try:
        #sometimes the homepage url points to the same page as the faculty profile page
        #which should be treated differently from an actual homepage
        ret_url = urllib.request.urlopen(bio_url).geturl() 
    except:
        return False       #unable to access bio_url
    urls = [re.sub('((https?://)|(www.))','',url) for url in [ret_url,dir_url]] #removes url scheme (https,http or www) 
    return not(urls[0]== urls[1])

#extracts all Faculty Profile page urls from the Directory Listing Page
def scrape_dir_page(dir_url,driver):
    print ('-'*20,'Scraping directory page','-'*20)
    faculty_links = []
    faculty_base_url = 'https://sc.edu'
    #execute js on webpage to load faculty listings on webpage and get ready to parse the loaded HTML 
    soup = get_js_soup(dir_url,driver)     
    for link_holder in soup.find_all('td', class_ = 'sorting_1'):
        rel_link = link_holder.find('a')['href'] #get url
        #url returned is relative, so we need to add base url
        faculty_links.append(faculty_base_url+rel_link) 
    print ('-'*20,'Found {} faculty profile urls'.format(len(faculty_links)),'-'*20)
    return faculty_links

def scrape_faculty_page(fac_url,driver):
    soup = remove_script(get_js_soup(fac_url,driver))
    each_bio = ''
    #scraber name
    profile_sec = soup.find('section', class_ = 'column grid_6')
    if profile_sec is not None:
        faculty_name = process_bio(profile_sec.find_all('h2')[0].get_text())
    #scrber bio    
    background_sec = soup.find('div', id = 'background')
    if background_sec is not None:
        for back_P in background_sec.find_all('p'):
            each_bio += process_bio(back_P.get_text())
    return faculty_name, fac_url, each_bio

dir_url = 'https://sc.edu/study/colleges_schools/hrsm/faculty-staff/' #url of directory listings of CS faculty
faculty_links = scrape_dir_page(dir_url,driver)


#faculty_links = ['https://sc.edu/study/colleges_schools/hrsm/faculty-staff/augur-tenney-zanne.php']


#Scrape homepages of all urls
faculty_name, faculty_urls, faculty_bios =[], [], []
tot_urls = len(faculty_links)
for i,link in enumerate(faculty_links):
    print ('-'*20,'Scraping faculty url {}/{}'.format(i+1,tot_urls),'-'*20)
    bio_name, bio_url, bio = scrape_faculty_page(link,driver)
    if bio.strip()!= '' and bio_url.strip()!='':
        faculty_urls.append(bio_url.strip())
        faculty_bios.append(bio.strip())
        faculty_name.append(bio_name.strip())
driver.close()
print(len(faculty_name), len(faculty_urls), len(faculty_bios))

transfer_to_csv = pd.DataFrame({
    'Faculty Name': faculty_name,
    'Faculty Link': faculty_urls,
    'Faculty Bios': faculty_bios
})
transfer_to_csv.to_csv('USC_bio_result.csv')

'''
def write_lst(lst,file_):
    with open(file_,'w') as f:
        for l in lst:
            f.write(l)
            f.write('\n')

bio_urls_file = 'bio_urls.txt'
bios_file = 'bios.txt'
write_lst(bio_urls,bio_urls_file)
write_lst(bios,bios_file)'''
