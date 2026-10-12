# cpulimit-ng (C) for loongarch64 — binary repack, tool only
include $(TOPDIR)/rules.mk

PKG_NAME:=cpulimit-ng
PKG_VERSION:=0.2
PKG_RELEASE:=1

PKG_SOURCE:=cpulimit-la-1.tar.gz
PKG_SOURCE_URL:=file:///home/yunix/istore-la-build/local-src/
PKG_HASH:=skip

PKG_BUILD_DIR:=$(BUILD_DIR)/$(PKG_NAME)-$(PKG_VERSION)-la
PKG_BINDIR:=$(BUILD_DIR)

include $(INCLUDE_DIR)/package.mk

define Package/cpulimit-ng
  SECTION:=utils
  CATEGORY:=Utilities
  TITLE:=CPU limiter (C)
endef

define Package/cpulimit-ng/description
  cpulimit-ng 龙芯版：交叉工具链编，musl 动态链接（解释器 ld-musl-loongarch64）。
endef

define Package/cpulimit-ng/install
	$(INSTALL_DIR) $(1)/usr/bin
	$(INSTALL_BIN) $(PKG_BINDIR)/cpulimit $(1)/usr/bin/
endef

define Build/Compile
endef

$(eval $(call BuildPackage,cpulimit-ng))
