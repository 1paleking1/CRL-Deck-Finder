import requests
from bs4 import BeautifulSoup
from pprint import pprint
import sys
import numpy as np
import re
import multiprocessing
import pyautogui as pg
import os
import colorama
from colorama import Fore, Style


colorama.init(autoreset=True)


# change working directory:
os.chdir(r"C:\Users\bossg\Documents\Sahil's work\Python Notes\Clash Royale Deck Finder")

################################################
# Functions:

def get_request(url, headers):
   r = requests.get(url=url, headers=headers)
   return r

def find_valid_bylevel(decks_list, num):

   valid_decks = []

   for deck in decks_list:
      
      fine = 0 # --> cards that are a good enough level

      for card in deck:

         try:

            if my_card_info[card][0] >= levels: # --> if the level is >= the set level
               fine += 1

            if fine >= num:   # was 5
               valid_decks.append(deck)
               break
   
         except KeyError: # --> skip cards that I don't have --> TODO: use the 'as e' format to catch only specific Key Errors (e.g. text)
            pass
   
   return valid_decks



def find_valid_bycard(decks_list, search):
   
   valid_decks = [deck for deck in decks_list if search in deck]
   return valid_decks   

################################################

# get token from binary file:
with open('token_bin.bin', encoding='utf-8') as file:
   TOKEN = file.read()



headers = {
   'Accept' : 'application/json',
   'authorization' : f'Bearer {TOKEN}' 
}


################################################
#TODO: 
# quit program if you click cancel
# format the final output to look nice
# add input for the player tag (text file to save the value so you don't have to enter every time)
   # asks 'is this you?' --> if no you enter a different tag


# INPUTS:

# get the level for most cards to be in a valid deck
# this code is used much later but I want the window to appear at the start (no need to wait for it)



# check if the tag in the text file is correct

with open('CrlPlayerTag.txt', 'r') as tag_file:
   my_tag = tag_file.read()
   tag_ans = pg.confirm(text=f'Proceed with tag:  {my_tag}?', title='Tag Selector', buttons=['Yes', 'Change Tag', 'Quit'])

# valid tag must have only:
   # Numbers: 0, 2, 8, 9
   # Letters: P, Y, L, Q, G, R, J, C, U, V

if tag_ans == 'Change Tag':
   
   check_ok = False
   while not check_ok:
      my_tag = pg.prompt(text='Enter your Tag (no #)', title='Changing Tag' , default='')
      my_tag = my_tag.upper()
      match = re.match(r'^[0289PYLQGRJCUV]*$', my_tag)
      is_match = bool(match)
      if is_match:
         check_ok = True

   
   with open('CrlPlayerTag.txt', 'w') as tag_file:
      tag_file.write(my_tag)


elif tag_ans == 'Quit':
   sys.exit(0) # --> successfully quit application




mode = pg.confirm(text='What Mode of Search?', title='Mode Selection', buttons=['Decks by level', 'Decks by Card', 'Quit'])

if mode == 'Decks by level':

   levels = pg.confirm(text='What deck level?', title='Level setter', buttons=['Any' ,'Tournament Standard\nlvl 9', 10, 11, 12, 13]) # --> get a level for most of the cards to be for a valid deck

   if levels == 'Tournament Standard\nlvl 9':
      levels = 9
   
   elif levels == 'Any':
      levels = 1

   levels = int(levels)

   num_minimum_level = pg.confirm(text=f'Minimum level {levels} Cards', title='Minimum Number', buttons=['4', '5', '6', '7', '8'])


elif mode == 'Decks by Card':

# validate the entered card --> only letters and spaces -- > allow dashes (X-Bow)
   check_ok = False
   while not check_ok:
      search_card = pg.prompt(text='Enter a Card Name', title='Decks by Card' , default='')

      if search_card.upper() == 'P.E.K.K.A': # --> one exception to the regex
         check_ok = True

      matched = re.match(r'^[a-zA-Z\s-]*$', search_card)
      is_matched = bool(matched)

      if is_matched:
         check_ok = True

   search_card = search_card.title()


elif mode == 'Quit':
   sys.exit(0)

################################################

# UK ID: 57000248
# US ID: 57000249

# --> how many top players?
check_ok = False
while not check_ok:
   limit = pg.prompt(text='How Many Players to Check? (1000 max, approx <1s per)', title='limit setter' , default='')
   if limit.isdigit() and int(limit) <= 1000:
      check_ok = True


location_id = 57000249 # --> top players in the US

location_id = pg.confirm(text=f'Location to Search', title='Location', buttons=['USA', 'UK', 'Italy', 'France'])

if location_id == 'USA':
   location_id = 57000249

elif location_id == 'UK':
   location_id = 57000248

elif location_id == 'Italy':
   location_id = 57000120

elif location_id == 'France':
   location_id = 57000087

else:
   raise Exception('Error assigning the location ID. Undefined Location?')




players_response = requests.get(f'https://api.clashroyale.com/v1/locations/{location_id}/rankings/players?limit={limit}', headers=headers)

json_data = players_response.json()

tags = np.array([player['tag'] for player in json_data['items']])
tags = [s.replace("#", "") for s in tags]



all_decks = []
proccesses = []

for tag in tags:

   p = multiprocessing.Process(target=get_request, args=[f'https://api.clashroyale.com/v1/players/%23{tag}/battlelog', headers])
   p.start()
   proccesses.append(p)



   team_cards_json = p.json()[0]['team']

   deck = np.array([card['name'] for card in team_cards_json[0]['cards']])

   all_decks.append(deck)

for p in proccesses:
   p.join()

# all decks contains the top player decks
#print(all_decks)


playerinfo_request = requests.get(f'https://api.clashroyale.com/v1/players/%23{my_tag}', headers=headers)

playerinfo_json = playerinfo_request.json()

my_card_info = {}

for card in playerinfo_json['cards']:
   my_card_info[card['name']] = [card['level'], card['count']]


###############################################

source = requests.get('https://statsroyale.com/cards').text
soup = BeautifulSoup(source, 'lxml')

groups = soup.find_all('div', class_='cards__cards')


info = []

for type in groups:
    for card in type:
        info.append(card)


for card in info:
   if card == '\n':
      info.remove(card)

del info[-1]
del info[-2]


info = [(str(i.div.text).strip(), i['data-rarity']) for i in info]

# info is now a list of tuples with the card and then the rarity as a number --> old levels system so has to be converted
###############################################

# converting to the new levels system:
for pair in info:

   try:

      if pair[1] == '4':
         my_card_info[pair[0]][0] += 8 # --> change a legendary card level to the new system

      elif pair[1] == '3':
         my_card_info[pair[0]][0] += 5 # --> epics
      
      elif pair[1] == '2': # --> rares
         my_card_info[pair[0]][0] += 2

         # commons are unchanged in the new system

   except KeyError:
      # card doesn't exist (I don't have it e.g. Inferno Dragon)
      pass

# all_card_info now has all of MY cards with their levels and how many I have

# check if a deck is valid according to my standards:
   # 5 or more card at level USABLE or more


if mode == 'Decks by level':
   
   valid_decks = find_valid_bylevel(all_decks, int(num_minimum_level))

elif mode == 'Decks by Card':
   valid_decks = find_valid_bycard(decks_list=all_decks, search=search_card)

# valid_decks is now a list of the decks that match my criteria

##########################################################
# finding the 'win-condition' cards:

source = requests.get('https://www.deckshop.pro/card/flag/win-condition').text
soup = BeautifulSoup(source, 'lxml')

non_win_cards = soup.find_all('img', class_='card opacity-20') # --> non-highlighted cards (not win conditions)
all_cards = soup.find_all('img', class_='card') # --> highlighted (win conditions)

wincondition_cards = [card['alt'] for card in all_cards if card not in non_win_cards]

wincondition_cards.extend(['P.E.K.K.A', 'Sparky', 'Mega Knight']) # --> 3 cards I think are win-conditions but not on the website

##########################################################
# total the number of each win-condition cards

wincondition_dict = {} # --> win-conditions and their counts

for deck in valid_decks:
   common_cards = list(set(wincondition_cards).intersection(set(deck))) # --> checks if the two lists have any common values (if there is a win condition card in the deck) with a set method
   if common_cards:
      for win_card in common_cards:
         if win_card in wincondition_dict:
            wincondition_dict[win_card] += 1
         elif win_card not in wincondition_dict:
            wincondition_dict[win_card] = 1

# sort the the dictionary into a list of tuples so the winconditions appear in decending order
wincondition_list = sorted(wincondition_dict.items(), key=lambda x: x[1], reverse=True)

##########################################################

# start outputing

print(Style.BRIGHT + f'\nDecks Found:   ' + f'{len(valid_decks)}\n')
print(Fore.MAGENTA + Style.BRIGHT + f'Deck Types:\n')

for win_card, number in wincondition_list: # --> print the number of different win conditions
   print(Fore.YELLOW + Style.BRIGHT + f'\t{win_card}:  ' + Fore.WHITE +Style.BRIGHT + f'{number}\n')


count = 1
for deck in valid_decks:
   print(Fore.GREEN + Style.BRIGHT + f'\n\tDeck {count}:\n')
   count += 1
   for card in deck:
      if card in wincondition_cards:
         print(Fore.YELLOW + Style.BRIGHT + card)
      else:
         print(Fore.CYAN + Style.BRIGHT + card)



pg.alert(text='Click OK to Quit', title='', button='OK')

sys.exit(0)
