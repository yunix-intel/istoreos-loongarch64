# webdav = hacdias/webdav = iStore 的 gowebdav 上游 (Go) for loongarch64
include $(TOPDIR)/rules.mk

PKG_NAME:=gowebdav
PKG_VERSION:=5.17.1
PKG_RELEASE:=1

PKG_SOURCE:=webdav-la-1.tar.gz
PKG_SOURCE_URL:=file:///home/yunix/istore-la-build/local-src/
PKG_HASH:=skip

PKG_BUILD_DIR:=$(BUILD_DIR)/$(PKG_NAME)-$(PKG_VERSION)-la
PKG_BINDIR:=$(BUILD_DIR)

include $(INCLUDE_DIR)/package.mk

define Package/webdav
  SECTION:=net
  CATEGORY:=Network
  TITLE:=WebDAV server (Go, gowebdav upstream)
  URL:=https://github.com/hacdias/webdav
endef

define Package/webdav/description
  webdav 龙芯版（即 gowebdav 上游 hacdias/webdav）：宿主 Go 直编。
  配置 /etc/webdav/config.yaml，按需填。
endef

define Package/webdav/install
	$(INSTALL_DIR) $(1)/usr/bin $(1)/etc/init.d $(1)/etc/webdav
	$(INSTALL_BIN) $(PKG_BINDIR)/webdav $(1)/usr/bin/
	$(INSTALL_BIN) ./files/webdav.init $(1)/etc/init.d/webdav
endef

define Build/Compile
endef

$(eval $(call BuildPackage,webdav))
