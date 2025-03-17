#!/usr/bin/env python3
"""
İskandinav içeriğini doğrudan vektör veritabanına indeksleyen script
"""
import os
import time
from app.embedding import chunk_document, save_chunks_to_db


def index_scandinavia_content():
    """İskandinav içeriğini doğrudan indeksler"""

    # Geçici dosya dizini oluştur
    temp_dir = "temp_docs"
    os.makedirs(temp_dir, exist_ok=True)

    # İçerik
    content = """
Scandinavia and the Nordic region are historical and geographical regions covering much of Northern Europe. Extending from above the Arctic Circle to the North and Baltic Seas, the Scandinavian Peninsula is the largest peninsula in Europe.

Popular tourist destinations Denmark, Norway, Sweden, Finland, Iceland, and on occasion, Greenland, all make up the Nordic countries. (Three of them took the top three spots on the United Nations' World Happiness Report in 2021, with Finland being number one for the fourth year in a row.) As a whole, Scandinavia has some of the most beautiful landscapes in the world and is enriched with its own culture and way of life, which draws in millions of people every year.

This guide includes everything you need to know to plan your trip, including the best time to visit, the top Scandinavian destinations, where to stay, what to eat, and money-saving tips in this often-pricy part of the world.

Planning Your Trip
Best Time to Visit: Because of the Nordic countries' locations, they have relatively long daylight hours in the summer and very short ones in the winter. Northern Norway and Finland experience almost no darkness during June and July. The summer season brings more stability in the weather, making it the perfect time to schedule outdoor adventures. The winter months are ideal for a quieter vacation and give the best opportunity to spot the Northern Lights because of the lack of light pollution.

Languages: Danish, Swedish, Norwegian, Icelandic, and Faroese.

Currency: Each country has its own unique currency. Denmark and Greenland both use the Danish krone. Finland uses the traditional European Euro. Norway uses the Norwegian krone, Sweden uses the Swedish krona, and Iceland uses the Icelandic krona.

Getting Around: It is relatively easy to make your way around Scandinavia. The region is driveable, so long as you have a valid license, passport, the car's registration and insurance, and are over the age of 18. The road rules are also similar to that of the U.S., making driving more straightforward than in other countries. However, train travel is just as popular in this area and can be cheaper. There are various rail passes you can get to explore the region, or you can take private train rides, such as the famous Flam rails.

Travel Tips: Make sure you pack a variety of clothing, as the weather in Scandinavia can vary between each country. Plan ahead for a trip to Scandanavia, as there are many cities to visit and even more to see and experience.

Places to Visit
Copenhagen, Denmark
Copenhagen offers unique museums that explore its Viking heritage, guided tours to help immerse travelers in its everyday life, and historical sites, such as Amalienborg Castle, where the royal family takes their winter holiday. Travelers can see the changing of the guard daily. Copenhagen is one of Scandinavia's most popular tourist destinations, and there is so much to do that no two days could be the same.

Bergen, Norway
Norway offers stunning cities where the scenery might take your breath away. The city of Bergen is one of Norway's most popular and scenic destinations, where you can peruse an old-timey fish market or enjoy buildings that date back to the 14th century. Don't forget to spend some time in the natural beauty of the mountains and fjords surrounding the city.

Stockholm, Sweden
Stockholm is a busy tourist attraction all on its own. The city is full of gorgeous sights and experiences, including two free beaches, several impressive churches, and Djurgården, a nature park on an island right in the middle of Stockholm.

Reykjavik, Iceland
Iceland's picturesque terrain is perfect for anyone who wants to earn some stunning photos. Travelers can visit the Blue Lagoon, a series of naturally-heated thermal pools near Iceland's capital Reykjavik. Some people say that bathing in the lagoon can help treat certain skin conditions - it's like visiting a spa minus the insane prices. Travelers can also enjoy whale watching on a whale safari, and depending on where you go and who you booked with, you might even have the opportunity to swim with the giant sea mammals.

Helsinki, Finland:
While less of a tourist attraction than some of the other Scandinavian capital cities, the capital city of Finland, Helsinki, offers some of its own top-notch attractions. Its most popular tourist attraction is the Suomenlinna Fortress, a UNESCO-designated historic site. It holds several shops, restaurants, and museums inside, including one housed in an old submarine. Close to the capital are more than 300 islands that bring in thousands of visitors for recreation and other entertainment throughout the year.

What to Eat and Drink
The Scandinavian and Nordic countries are well known for their delicious foods, and each country has its own special something to offer up.

Sweden's cuisine includes the famous Swedish meatballs, cinnamon rolls, and smörgåstårta (sandwich cake).
Finnish foods include lohikeitto (salmon soup) and reindeer meat.
Norway's national dish, Fårikål, is mutton and cabbage. Aquavit is a popular alcoholic beverage.
Denmark offers delicious sweets like flodebolle (chocolate-covered marshmallow treats).
Iceland is known for seafood including puffin, whale, and fermented shark.

Money Saving Tips
Enjoy all of the free things that Scandanavia offers, including its three most extraordinary natural phenomena, the Northern Lights (Aurora Borealis), the Midnight Sun, and the Polar Nights.
Scandanavia's casual cafes and bars usually offer very filling meals for a relatively low cost.
Look into getting a city card in Sweden or Norway for discounts on tourist attractions.
Use debit and credit cards instead of ATMs to save on fees.
"""

    # Belge oluştur
    doc_id = "scandinavia_travel_guide"
    title = "Scandinavia and the Nordic Region: Planning Your Trip"

    # Belgeyi parçalara böl
    chunks = chunk_document(content, title)

    # Parçaları veritabanına kaydet
    print(f"'{doc_id}' belgesi {len(chunks)} parçaya bölündü, veritabanına kaydediliyor...")
    count = save_chunks_to_db(doc_id, chunks)

    print(f"İşlem tamamlandı! {count} belge parçası başarıyla indekslendi.")


if __name__ == "__main__":
    index_scandinavia_content()