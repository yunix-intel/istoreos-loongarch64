# lucky (Go) for loongarch64 — binary repack
include $(TOPDIR)/rules.mk

PKG_NAME:=lucky
PKG_VERSION:=2.27.2
PKG_RELEASE:=1

PKG_SOURCE:=lucky-la-1.tar.gz
PKG_SOURCE_URL:=file:///home/yunix/istore-la-build/local-src/
PKG_HASH:=skip

PKG_BUILD_DIR:=$(BUILD_DIR)/$(PKG_NAME)-$(PKG_VERSION)-la
PKG_BINDIR:=$(BUILD_DIR)

include $(INCLUDE_DIR)/package.mk

define Package/lucky
  SECTION:=net
  CATEGORY:=Network
  TITLE:=Lucky helper (Go)
  URL:=https://github.com/gdy666/lucky
endef

define Package/lucky/description
  lucky 龙芯版：宿主 Go 直编，静态链接。
endef

define Package/lucky/install
	$(INSTALL_DIR) $(1)/usr/bin $(1)/etc/init.d
	$(INSTALL_BIN) $(PKG_BINDIR)/lucky $(1)/usr/bin/
	$(INSTALL_BIN) ./files/lucky.init $(1)/etc/init.d/lucky
endef

define Build/Compile
endef

$(eval $(call BuildPackage,lucky))
