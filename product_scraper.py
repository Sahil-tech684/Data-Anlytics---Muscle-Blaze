# Required Libraries
import json
import scrapy
from scrapy.crawler import CrawlerProcess
from warnings import filterwarnings
filterwarnings('ignore')

# Spider
class WheyProteinSpider(scrapy.Spider):
    name = 'WheyProteinSpider'
    base_url = 'https://www.muscleblaze.com'

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0'
    }

    custom_settings = {
        'FEED_FORMAT': 'json',
        'FEED_URI': 'whey_data.json',
        'CONCURRENT_REQUESTS': 32,
        # 'LOG_LEVEL': 'ERROR'
    }

    def start_requests(self):
        yield scrapy.Request(
            url= 'https://www.muscleblaze.com/veronica/catalog/results/CL-1703?pageNo=1&perPage=1000&excludeOOS=true&plt=1&st=9',
            headers= self.headers,
            callback= self.parse_homepage
        )

    def parse_homepage(self, response):
        res = response.json()
        self.logger.info(f"Total {len(res['results']['variants'])} products found.")

        for product in res['results']['variants']:
            yield scrapy.Request(
                url= self.base_url + f'/{"sv" if not product["pk_type"] else "pk"}' + product['urlFragment'] + '?navKey=' + product['navKey'],
                headers= self.headers,
                callback= self.parse_product_page,
                meta= {
                    'data': self.get_required_data_fields(product= product)
                }
            )

    def parse_product_page(self, response):
        res = json.loads(response.xpath("//script[@id='__NEXT_DATA__']/text()").get())
        product = res['props']['pageProps']['data']['results']
        
        if response.meta['data']['isReviewEnabled']: 
            yield scrapy.Request(
                url= f'https://www.muscleblaze.com/veronica/variant/review/{product["review_slug"]}/results/allReviews?pageNo=1&perPage=100000&storeId=1&srtType=1&plt=1&st=9',
                headers= self.headers,
                callback= self.parse_product_reviews,
                meta= {
                    'data': self.update_product_details(past_product_details= response.meta['data'], product= product)
                }
            )
        else:
            yield self.update_product_details(past_product_details= response.meta['data'], product= product)
        

    def parse_product_reviews(self, response):
        res = response.json()['results']
        response.meta['data']['totalReviews'] = res['ttl_rvws']

        yield response.meta['data'] | {
            'no_feat_rtng': res['no_feat_rtng'],
            'review_features': res['feature'],
            'reviews': [{
                'id': review['id'],
                'date': review['rvw_dt'],
                'userName': review['user'],
                'rating': review['rtng'],
                'title': review['title'],
                'review': review['review'],
                'productId': review['sv_id'],
                'productName': review['sv_nm'],
                'productId': review['sv_id'],
                'isCertified': review['cert'],
                'isExpert': review['expert'],
                'totalVotes': review['ttl_vt'],
                'positiveVotes': review['pstv_vt'],
                'negativeVotes': review['ttl_vt'] - review['pstv_vt'],
                'featureWiseRating': review['pfr'],
            } for review in res['sv_rvw']]
        }

    def get_required_data_fields(self, product):
        return {
            'id': product['id'],
            'rank': product['rank'],
            'name': product['nm'].strip(),
            'weight': product['selAttr']['gen-pro-siz'],
            'flavour': product['selAttr']['gen-sn-flv'],
            'supplimentName': product['spName'],
            'categoryName': product['catName'],
            'secondaryCategory': product['secondary_category'],
            'description': None,
            'isPack': product['pk_type'],
            'isJustLaunched': product['justLaunched'],
            'isPublished': None,
            'isExclusiveVariant': product['isExclusiveVariant'],
            'productPageCreatedAt': None,
            'goal': product['goal'],
            'consumedWith': product['consumed_with'],
            'Attributes': {
                attribute['dis_nm']: [i['val'] for i in attribute['values']]
                for attribute in product['hghAttr']
            },
            'vendorId': product['vendorId'],
            'vendorName': product['vendorName'],
            'brandName': product['brName'],
            'marketedBy': None,
            'manufacturer': None,
            'mrp': product['mrp'],
            'offerPrice': product['offer_pr'],
            'mrpOfferPriceDiff': product['mrpOfferPriceDiff'],
            'discount': product['discount'],
            'currDiscountPercent': product['currDisPercent'],
            'isReviewEnabled': product['reviewEnabled'],
            'rating': product['rating'],
            'totalRating': product['ttl_rtng'],
            'totalReviews': product['nrvw'],
            'reviewSlug': product['review_slug'],
            'isPreOrderAllowed': product['preOrdrAlwd'],
            'vendorHkFulfilled': product['vendorHkFulfilled'],
            'isOrderEnabled': product['ordrEnbld'],
            'returnDays': product['returnDays'],
            'numberOfOffers': product['numberOfOffers'],
            'tags': product['varTag']['tags'],
            'isConsultProduct': product['isConsultProduct'],
            'percentClaimed': product['percent_claimed'],
            'infoTags': product['infoTags'],
            'expiryDate': product['expiry_date'],
            'loyaltyPercent': None,
            'keyPoint1': product['kp1'],
            'keyPoint2': product['kp2'],
            'keyPoint3': product['kp3'],
            'keyPoint4': product['kp4'],
            'keyPoint5': product['kp5'],
            'storeVariantIdsInPack': product['storeVariantIdsInPack'],
            'groups': {
                group['dis_nm']: [
                    {'key': i['dis_nm'], 'val': i['val']} 
                    for i in group['values']
                ] 
                for group in product['grps']
            },
            'url': self.base_url + f'/{"sv" if not product["pk_type"] else "pk"}' + product['urlFragment'] + '?navKey=' + product['navKey']
        }

    def update_product_details(self, product, past_product_details):
        past_product_details['description'] = [i['attributeArea'] for i in product['page']['pgSections'][0]['scContent'] if i['dis_nm'] == 'Product Detail'][0][0]['value'] if 'page' in product and product['page']['pgSections'] and [i['attributeArea'] for i in product['page']['pgSections'][0]['scContent'] if i['dis_nm'] == 'Product Detail'] else None
        past_product_details['isPublished'] = product['is_published'] if 'is_published' in product else past_product_details['isPublished']
        past_product_details['marketedBy'] = product['marketedBy'] if 'marketedBy' in product else past_product_details['marketedBy']
        past_product_details['manufacturer'] = product['manufacturerDtl'] if 'manufacturerDtl' in product else past_product_details['manufacturer']
        past_product_details['productPageCreatedAt'] = product['createDt'] if 'createDt' in product else past_product_details['productPageCreatedAt']
        past_product_details['reviewSlug'] = product['review_slug'] if 'review_slug' in product else past_product_details['reviewSlug']
        past_product_details.update({
            'loyaltyPercent': product['loyaltyPercent'] if 'loyaltyPercent' in product else None,
            'offerAllowed': product['offerAllowed'] if 'offerAllowed' in product else None,
            'primaryCategoryRank': product['primaryCategoryRank'] if 'primaryCategoryRank' in product else None,
            'secondaryCategoryRank': product['secondaryCategoryRank'] if 'secondaryCategoryRank' in product else None,
            'leafCategoryRank': product['leafCategoryRank'] if 'leafCategoryRank' in product else None,
            'freebieNm': product['freebieNm'] if 'freebieNm' in product else None,
            'freebieDetails': product['freebieDetails'] if 'freebieDetails' in product else None,
            'flashDealActive': product['flashDealActive'] if 'flashDealActive' in product else None,
            'loyaltyCash': product['loyaltyCash'] if 'loyaltyCash' in product else None,
            'batches': product['batches'] if 'batches' in product else None,
            'ingredients': product['ingredients'] if 'ingredients' in product else None,
            'fssaiCode': product['fssai_code'] if 'fssai_code' in product else None,
            'isEmiAvailable': product['emiAvail'] if 'emiAvail' in product else None,
            'emiStartsWith': product['emiStartsWith'] if 'emiStartsWith' in product else None,
            'emiOptions': [i['name'] for i in product['emiInquiry']['options']] if 'emiInquiry' in product and product['emiInquiry'] else None,
            'paymentOffers': product['paymentOffers'] if 'paymentOffers' in product else None,
            'paymentModes': product['paymentModes'] if 'paymentModes' in product else None,
            'isKitVariant': product['kit_variant'] if 'kit_variant' in product else None,
            'isNutrapack': product['isNutrapack'] if 'isNutrapack' in product else None,
            'country': product['country'] if 'country' in product else None,
            'shelfLife': product['shelf_life'] if 'shelf_life' in product else None,
            'importedBy': product['importedBy'] if 'importedBy' in product else None,
            'maxDispatch': product['max_dsptch'] if 'max_dsptch' in product else None,
            'isBestPrice': product['isBestPrice'] if 'isBestPrice' in product else None,
            'lastUpdatedAt': product['updateDt'] if 'updateDt' in product else None,
            'pageSeo': product['page']['pgSeo'] if 'page' in product else None,
        })
        return past_product_details



if __name__ == '__main__':
    process = CrawlerProcess()
    process.crawl(WheyProteinSpider)
    process.start()