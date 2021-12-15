from bs4 import BeautifulSoup
import bs4
from pprint import pprint

from Constants import *



__basic_info_box_selectors = {
	"info-box": "table.infobox",
	"caption": "caption.infobox-title",
	"section": "tr",
	"big-section": "td.infobox-image",
	"logo": "a.image img",
	"boxscore": "td.infobox-full-data",
	"boxscore-row": "table > tbody > tr",
	"small-section-header": "th.infobox-header",
	"small-section-label": "th.infobox-label",
	"small-section-value": "td.infobox-data",
}





def process_basic_info_box(soup):
	processed_info = dict()

	selectors = __basic_info_box_selectors
	
	infobox = None
	infoboxes = soup.select(selectors["info-box"])
	if infoboxes: infobox = infoboxes[0]

	if infobox:
		caption = infobox.select(selectors["caption"])
		if caption: processed_info["caption"] = caption[0].text
		
		# Find boxscore
		boxscoreNode = None
		boxscoreNodes = infobox.select(selectors["boxscore"]) # td.infobox-full-data
		if boxscoreNodes:
			boxscoreNode = boxscoreNodes[0]

		sectionNodes = infobox.select(selectors["section"]) # tr
		bigSectionNodes = infobox.select(selectors["big-section"]) # td.infobox-image
		if bigSectionNodes:
			for i in range(0, len(bigSectionNodes)):
				bigSectionNode = bigSectionNodes[i]

				# Find Logo
				logoNodes = bigSectionNode.select(selectors["logo"])
				if logoNodes:
					logoNode = logoNodes[0]
					logoThumbSrc = logoNode.attrs["src"]
					logoUrl = extract_image_url(logoThumbSrc)
					processed_info.setdefault("logo", logoUrl)
					continue

				# Find boxscore
				if not boxscoreNode: # Because Pro Bowl gotta be different
					if i == (len(bigSectionNodes) - 1):
						boxscoreNode = bigSectionNode


		sectionHeaderLabel = ""
		for sectionNode in sectionNodes: #tr (including big sections)
			sectionHeaderNodes = sectionNode.select(selectors["small-section-header"])
			if sectionHeaderNodes:
				sectionHeaderLabel = sectionHeaderNodes[0].text;
				continue

			labelNodes = sectionNode.select(selectors["small-section-label"])
			if labelNodes:
				label = labelNodes[0].text
				valueNode = None
				value = None
				valueNodes = sectionNode.select(selectors["small-section-value"])
				if valueNodes:
					valueNode = valueNodes[0]

					if (label == "Date"):
						value = valueNode.text.strip()
						eventDate = None
						try: eventDate = datetime.datetime.strptime(value, "%B %d, %Y").date()
						except ValueError:
							try: eventDate = datetime.datetime.strptime(value, "%a, %B %d, %Y").date()
							except ValueError:
								try: eventDate = datetime.datetime.strptime(value, "%A, %B %d, %Y").date()
								except ValueError: pass

						if eventDate:
							processed_info.setdefault("date", eventDate)
					if (label == "Television" or (label == "Network" and ((not sectionHeaderLabel) or sectionHeaderLabel.find("TV") >= 0))):
						networks = []
						parenState = 0
						contents = flatten_children(valueNode)
						for contentNode in contents:
							nodeText = ""
							if isinstance(contentNode, bs4.Tag):
								if contentNode.name == "a" and parenState == 0:
									networks.append(contentNode.text)
									continue
								else:
									nodeText = contentNode.text
							elif isinstance(contentNode, basestring):
								nodeText = str(contentNode)

							# For now, we're going to assume that all networks are hyperlinked
							if nodeText: # Scan characters, tracking open and closed parens
								for c in nodeText:
									if c == "(": parenState = parenState + 1
									elif c == ")": parenState = parenState - 1
									# TODO: We'll do more sophisticated parsing later

						processed_info.setdefault("networks", list(set(networks)))

					processed_info.setdefault(("inspected:%s" % label), valueNode.text)
		
		pass			
					
		if boxscoreNode:
			awayTeam = None
			homeTeam = None

			for boxscoreRow in boxscoreNode.select(selectors["boxscore-row"]):
				for boxscoreContent in boxscoreRow.contents:
					if not isinstance(boxscoreContent, (bs4.Tag)): continue
					if boxscoreContent.name != "td": break

					teamName = boxscoreContent.text
					if awayTeam == None:
						awayTeam = teamName
						break
					if homeTeam == None:
						homeTeam = teamName
						break

			processed_info.setdefault("homeTeam", homeTeam)
			processed_info.setdefault("awayTeam", awayTeam)
			
			pass


	return processed_info


def get_first_paragraph(soup):
	blurbNode = None
	infoBox = soup.select_one(__basic_info_box_selectors["info-box"])
	if infoBox:
		blurbNode = infoBox.find_next_sibling("p")
	if blurbNode:
		return strip_citations(blurbNode).strip().replace("  ", " ")
	return None


def extract_image_url(thumbUrl):
	imgUrl = thumbUrl[0:]

	imgUrl = "/".join(imgUrl.split("/")[0:-1])
	imgUrl = imgUrl.replace("/thumb/", "/")
	if imgUrl[0:2] == "//": imgUrl = "https:" + imgUrl
	if imgUrl[0:1] == "/": imgUrl = "https://upload.wikimedia.org" + imgUrl

	return imgUrl


def merge_dictionaries(dct, into):
	if into == None or not dct: return into

	for key in dct.keys():
		value = dct[key]
		if not key in into.keys(): into.setdefault(key, value)
		elif into[key] == None: into[key] = value
		if isinstance(into[key], (dict)): merge_dictionaries(value, into[key])

	return into


def get_toc_link_text(a):
	tocText = a.text
	tocTextNodes = a.select("span.toctext")
	if tocTextNodes: tocText = tocTextNodes[0].text
	return tocText


def get_section_caption(soup, anchorID):
	anchorPoint = soup.find(id=anchorID)
	#anchorPoint = soup.select_one("#%s" % anchorID.strip())
	if anchorPoint:
		return anchorPoint.text
	return None

#SelectorSyntaxError



def get_blurb(soup, anchorID):
	blurbNode = None
	anchorPoint = soup.find(id=anchorID)
	#anchorPoint = soup.select_one("#%s" % anchorID.strip())
	heading = anchorPoint.parent
	for sibling in heading.find_next_siblings():
		if not isinstance(sibling, bs4.Tag): continue
		if sibling.name == heading.name: break;
		if sibling.name == "p":
			blurbNode = sibling
			break
	if blurbNode:
		return strip_citations(blurbNode).strip().replace("  ", " ")
	return None


def strip_citations(el):
	elementText = ""

	for child in el.children:
		if isinstance(child, (basestring)):
			elementText += child
			continue;

		if isinstance(child, (bs4.Tag)):
			if child.name == "sup" and child.attrs.get("class") and "reference" in child.attrs["class"]:
				continue

			elementText += strip_citations(child)

	return elementText


def flatten_children(el, lst=None):
	if el == None: return lst
	if lst == None: lst = list()

	for child in el.children:
		lst.append(child)
		if isinstance(child, (bs4.Tag)): flatten_children(child, lst)

	return lst
