#!/bin/bash


IQURL=http://localhost:8070
IQUSER=admin
IQPWD=admin123

APP_NAME=conanapp

COMP_CHANNEL=stable
COMP_NAME=zlib
COMP_OWNER=conan
COMP_VERSION=1.2.11
LICENSE_IDS='"AGEL","Amazon","AGPL-2.0","Beerware","BSD-4-Clause"'


  curl -u ${IQUSER}:${IQPWD} "http://localhost:8070/rest/licenseOverride/application/${APP_NAME}?timestamp=1628261042339" \
  -H 'Connection: keep-alive' \
  -H 'sec-ch-ua: " Not;A Brand";v="99", "Google Chrome";v="91", "Chromium";v="91"' \
  -H 'Accept: application/json, text/plain, */*' \
  -H 'X-CSRF-TOKEN: d8418ba0-5f53-4099-b9e3-7800e20857c3' \
  -H 'sec-ch-ua-mobile: ?0' \
  -H 'User-Agent: Mozilla/5.0 (X11; Fedora; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.106 Safari/537.36' \
  -H 'Content-Type: application/json;charset=UTF-8' \
  -H 'Origin: http://localhost:8070' \
  -H 'Sec-Fetch-Site: same-origin' \
  -H 'Sec-Fetch-Mode: cors' \
  -H 'Sec-Fetch-Dest: empty' \
  -H 'Referer: http://localhost:8070/assets/index.html' \
  -H 'Accept-Language: en-US,en;q=0.9' \
  -H 'Cookie: _ga=GA1.1.2056190521.1597258316; _pendo_meta.8dc60703-c661-4e2c-7231-fa19f57473c3=2365755608; CLM-CSRF-TOKEN=d8418ba0-5f53-4099-b9e3-7800e20857c3; CLMSESSIONID=a0ec91691eca45f2bbabb0e228426a51; apt.sid=AP-GAADVBJPNBLE-2-1628260704075-11423853; apt.uid=AP-GAADVBJPNBLE-2-1628260704075-81338674.0.2.c998a353-7e04-435d-97c9-6d7cd1b35793; IQ-SESSION-EXPIRATION-TIMESTAMP=1628262841375' \
  --data-raw "{\"id\":null,\"ownerId\":\"${APP_NAME}\",\"componentIdentifier\":{\"format\":\"conan\",\"coordinates\":{\"channel\":\"${COMP_CHANNEL}\",\"name\":\"${COMP_NAME}\",\"owner\":\"${COMP_OWNER}\",\"version\":\"${COMP_VERSION}\"}},\"status\":\"OVERRIDDEN\",\"licenseIds\":[${LICENSE_IDS}],\"comment\":\"\"}" \
  --compressed


