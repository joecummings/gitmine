from furl import furl

BASE_GH_API = "https://api.github.com"
ISSUES_ENDPOINT = furl(BASE_GH_API, path="/issues")
REPOS_ENDPOINT = furl(BASE_GH_API, path="/repos")
SEARCH_ENDPOINT = furl(BASE_GH_API, path="/search")
USER_ENDPOINT = furl(BASE_GH_API, path="/user")
