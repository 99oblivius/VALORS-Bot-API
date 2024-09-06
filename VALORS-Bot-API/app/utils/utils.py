import hmac
from fastapi import HTTPException
from urllib.parse import urlparse, urlencode, parse_qs, urlunparse

def resize_image_url(url: str, size: int=64):
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    query_params['size'] = [str(size)]
    new_query = urlencode(query_params, doseq=True)
    new_url = urlunparse((
        parsed_url.scheme,
        parsed_url.netloc,
        parsed_url.path,
        parsed_url.params,
        new_query,
        parsed_url.fragment
    ))
    
    return new_url