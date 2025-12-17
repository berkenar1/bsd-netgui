PORTNAME=      bsd-netgui
PORTVERSION=   0.1.0
CATEGORIES=    net-mgmt sysutils python
MASTER_SITES=  PYPI
PKGNAMEPREFIX= ${PYTHON_PKGNAMEPREFIX}

MAINTAINER=    you@example.com
COMMENT=       GUI network management tool for FreeBSD and other BSD systems
WWW=           https://github.com/berkenar1/bsd-netgui

LICENSE=       MIT
LICENSE_FILE=  ${WRKSRC}/LICENSE

USES=          python:3.8+ shebangfix
USE_PYTHON=    distutils autoplist

# If your shebangs use /usr/bin/env python3
SHEBANG_FILES= bsd_netgui/*.py bsd_netgui/*/*.py

RUN_DEPENDS=   ${PYTHON_PKGNAMEPREFIX}wxPython4>0:x11-toolkits/py-wxPython4@${PY_FLAVOR} \
               ${PYTHON_PKGNAMEPREFIX}psutil>0:sysutils/py-psutil@${PY_FLAVOR} \
               ${PYTHON_PKGNAMEPREFIX}netifaces>0:net/py-netifaces@${PY_FLAVOR}

# If you do not publish to PyPI yet, use GitHub instead:
# USE_GITHUB=  yes
# GH_ACCOUNT=  berkenar1
# GH_PROJECT=  bsd-netgui
# GH_TAGNAME=  <tag or commit>

NO_ARCH=       yes

.include <bsd.port.mk>
