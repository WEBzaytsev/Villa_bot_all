# imports
import json
from time import sleep
from uuid import uuid4

import requests

from proxy import Rotator, proxies

rotator = Rotator(proxies)


def get_product_detail_page(targetId, fb_dtsg=None):
    random_uuid = str(uuid4())
    variables = {
        "UFI2CommentsProvider_commentsKey": "MarketplacePDP",
        "canViewCustomizedProfile": True,
        "feedbackSource": 56,
        "feedLocation": "MARKETPLACE_MEGAMALL",
        "location_latitude": -8.65583333,
        "location_longitude": 115.13416667,
        "location_radius": 5,
        "location_vanity_page_id": "107286902636860",
        "pdpContext_isHoisted": False,
        "pdpContext_trackingData": f"browse_serp:{random_uuid}",
        "referralCode": None,
        "relay_flight_marketplace_enabled": False,
        "removeDeprecatedCommunityRecommended": False,
        "scale": 2,
        "should_show_new_pdp": False,
        "targetId": str(targetId),
        "useDefaultActor": False
    }
    doc_id = 6365444460151213
    additional_payload = {
        '__a': 1,
        '__comet_req': 2,
    }
    req = graphql_request(doc_id, variables, fb_dtsg, additional_payload)
    if req:
        return req
    return None


def init_search(query, fb_dtsg=None):
    """
    CometMarketplaceSearchContentContainerQuery
    """

    variables = {
        "buyLocation": {
            "latitude": -8.65583333,
            "longitude": 115.13416667
        },
        "contextual_data": None,
        "count": 24,
        "cursor": None,
        "flashSaleEventID": "",
        "hasFlashSaleEventID": False,
        "marketplaceSearchMetadataCardEnabled": False,
        "params": {
            "bqf": {
                "callsite": "COMMERCE_MKTPLACE_WWW",
                "query": str(query)
            },
            "browse_request_params": {
                "commerce_enable_local_pickup": True,
                "commerce_enable_shipping": True,
                "commerce_search_and_rp_available": True,
                "commerce_search_and_rp_category_id": [],
                "commerce_search_and_rp_condition": None,
                "commerce_search_and_rp_ctime_days": None,
                "filter_location_latitude": -8.65583333,
                "filter_location_longitude": 115.13416667,
                "filter_price_lower_bound": 0,
                "filter_price_upper_bound": 214748364700,
                "filter_radius_km": 5,
                # "commerce_search_sort_by":"CREATION_TIME_DESCEND"
            },
            "custom_request_params": {
                "browse_context": None,
                "contextual_filters": [],
                "referral_code": None,
                "saved_search_strid": None,
                "search_vertical": "C2C",
                "seo_url": None,
                "surface": "SEARCH",
                "virtual_contextual_filters": []
            }
        },
        "savedSearchID": None,
        "savedSearchQuery": str(query),
        "scale": 1,
        "shouldIncludePopularSearches": False,
        "topicPageParams": {
            "location_id": "117591911630921",
            "url": None
        },
        "vehicleParams": ""
    }
    additional_payload = {
        '__a': 1,
        '__comet_req': 2,
    }
    doc_id = 6238687802818710
    req = graphql_request(doc_id, variables, fb_dtsg, additional_payload)

    return req


def cursor_search(query, cursor="", fb_dtsg=None):
    """
    CometMarketplaceSearchContentPaginationQuery
    """

    doc_id = 5100858473347890

    variables = {
        "count": 24,
        "cursor": cursor,
        "params": {
            "bqf": {
                "callsite": "COMMERCE_MKTPLACE_WWW",
                "query": f"{query}"
            },
            "browse_request_params": {
                "commerce_enable_local_pickup": True,
                "commerce_enable_shipping": True,
                "commerce_search_and_rp_available": True,
                "commerce_search_and_rp_category_id": [],
                "commerce_search_and_rp_condition": None,
                "commerce_search_and_rp_ctime_days": None,
                "filter_location_latitude": -8.65583333,
                "filter_location_longitude": 115.13416667,
                "filter_price_lower_bound": 0,
                "filter_price_upper_bound": 214748364700,
                "filter_radius_km": 5
            },
            "custom_request_params": {
                "browse_context": None,
                "contextual_filters": [],
                "referral_code": None,
                "saved_search_strid": None,
                "search_vertical": "C2C",
                "seo_url": None,
                "surface": "SEARCH",
                "virtual_contextual_filters": []
            }
        },
        "scale": 1
    }
    additional_payload = {
        '__a': 1,
        '__comet_req': 2,
    }
    req = graphql_request(doc_id, variables, fb_dtsg, additional_payload)
    return req


next_page = None


def search_continious(query, lat=None, lon=None, iterations=1, fb_dtsg=None):
    global next_page
    page = 0
    if iterations:
        page += 1
        first_page = init_search(query)
        listing_ids = []
        errors = first_page.get('errors', False)
        data = first_page.get('data', False)
        if errors and not data:
            print(f"Error: {errors[0]['message']}")
            return listing_ids
        for edge in data['marketplace_search']['feed_units']['edges']:
            if edge['node']['story_type'] in ['SERP_HEADER', 'SERP_NO_RESULTS']:
                return listing_ids
            listing_ids.append(edge['node']['listing']['id'])
        end_cursor = data['marketplace_search']['feed_units']['page_info']['end_cursor']
        while page != iterations:
            page += 1
            next_page = cursor_search(query, cursor=end_cursor)
            errors = next_page.get('errors', False)
            data = next_page.get('data', False)
            if errors and not data:
                print(f"Error: {errors[0]['message']}")
                return listing_ids
            if data['marketplace_search']['feed_units']['edges']:
                if edge['node']['story_type'] in ['SERP_HEADER', 'SERP_NO_RESULTS']:
                    return listing_ids
                end_cursor = data['marketplace_search']['feed_units']['page_info']['end_cursor']
                for edge in data['marketplace_search']['feed_units']['edges']:
                    listing_ids.append(edge['node']['listing']['id'])
            else:
                return listing_ids
    return listing_ids
    # listing_ids.append(edge['node']['listing']['id'])
    # cursor =
    # for elem in
    # page += 1
    # if page > 1:


def parse_feed_units(content):
    pass


def graphql_request(method, variables, fb_dtsg=None, additional_payload=None):
    url = 'https://en-gb.facebook.com/api/graphql/'
    headers = {
        "content-type": "application/x-www-form-urlencoded",
        "user-agent": "Mozilla/5.0 (Linux; Android 11; SAMSUNG SM-A505FM) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/12.1 Chrome/79.0.3945.136 Mobile Safari/537.36"
    }
    payload = {
        'variables': json.dumps(variables, separators=(',', ':')),
        'doc_id': str(method)
    }
    if fb_dtsg:
        payload['fb_dtsg'] = fb_dtsg
    if additional_payload:
        payload = additional_payload | payload
    proxy = rotator.get()
    if not proxy:
        print('No alive proxy left. Sleeping for 24 hours.')
        sleep(86400)
        return graphql_request(method, variables, fb_dtsg, additional_payload)
    proxy_list = {'http': str(proxy), 'https': str(proxy)}
    try:
        req = requests.post(url, headers=headers, data=payload,
                            proxies=proxy_list, timeout=15)
    except (requests.exceptions.ConnectionError, requests.exceptions.ConnectTimeout, requests.exceptions.ProxyError) as e:
        print(f"Error: {e}")
        proxy.status = "dead"
        return graphql_request(method, variables, fb_dtsg, additional_payload)
    errors = req.json().get('errors', False)
    if errors:
        print(f"Error: {errors[0]['message']}")
        proxy.status = "ratelimited"
        return graphql_request(method, variables, fb_dtsg, additional_payload)
    else:
        proxy.status = "ok"
    return req.json()


def get_location(query, fb_dtsg=None):
    variables = {
        "params": {
            "caller": "MARKETPLACE",
            "country_filter": None,
            "integration_strategy": "STRING_MATCH",
            "page_category": [
                "CITY",
                "SUBCITY",
                "NEIGHBORHOOD",
                "POSTAL_CODE"
            ],
            "query": str(query),
            "search_type": "PLACE_TYPEAHEAD",
            "viewer_coordinates": None
        }
    }
    additional_payload = {
        '__a': 1,
        '__comet_req': 15,
    }
    doc_id = 7321914954515895
    req = graphql_request(doc_id, variables, fb_dtsg, additional_payload)
    try:
        location_id = req['data']['city_street_search']['street_results']['edges'][0]['node']['page']['id']
        lat = req['data']['city_street_search']['street_results']['edges'][0]['node']['location']['latitude']
        lon = req['data']['city_street_search']['street_results']['edges'][0]['node']['location']['longitude']
        return location_id, lat, lon
    except:
        return None, None, None
