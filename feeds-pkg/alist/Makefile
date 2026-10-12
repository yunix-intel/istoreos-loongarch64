# alist (Go) for loongarch64 — binary repack
include $(TOPDIR)/rules.mk

PKG_NAME:=alist
PKG_VERSION:=3.64.0
PKG_RELEASE:=1

PKG_SOURCE:=alist-la-1.tar.gz
PKG_SOURCE_URL:=file:///home/yunix/istore-la-build/local-src/
PKG_HASH:=skip

PKG_BUILD_DIR:=$(BUILD_DIR)/$(PKG_NAME)-$(PKG_VERSION)-la
PKG_BINDIR:=$(BUILD_DIR)

include $(INCLUDE_DIR)/package.mk

define Package/alist
  SECTION:=net
  CATEGORY:=Network
  TITLE:=File list/browser (Go)
  URL:=https://github.com/AlistGo/alist
endef

define Package/alist/description
  alist 龙芯版：宿主 Go 直编，静态链接。数据目录 /etc/alist，首次跑 admin 初始化。
endef

define Package/alist/install
	$(INSTALL_DIR) $(1)/usr/bin $(1)/etc/init.d
	$(INSTALL_BIN) $(PKG_BINDIR)/alist $(1)/usr/bin/
	$(INSTALL_BIN) ./files/alist.init $(1)/etc/init.d/alist
endef

define Build/Compile
endef

$(eval $(call BuildPackage,alist))
