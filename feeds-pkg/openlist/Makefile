# openlist (Go) for loongarch64 — binary repack (self-built static; upstream only ships glibc)
include $(TOPDIR)/rules.mk

PKG_NAME:=openlist
PKG_VERSION:=4.2.6
PKG_RELEASE:=1

PKG_SOURCE:=openlist-la-1.tar.gz
PKG_SOURCE_URL:=file:///home/yunix/istore-la-build/local-src/
PKG_HASH:=skip

PKG_BUILD_DIR:=$(BUILD_DIR)/$(PKG_NAME)-$(PKG_VERSION)-la
PKG_BINDIR:=$(BUILD_DIR)

include $(INCLUDE_DIR)/package.mk

define Package/openlist
  SECTION:=net
  CATEGORY:=Network
  TITLE:=Cloud disk mount (Go)
  URL:=https://github.com/OpenListTeam/OpenList
endef

define Package/openlist/description
  openlist 龙芯版：上游只发 glibc 版（musl 跑不了），宿主 Go 重编静态版。
  数据目录 /etc/openlist，http://网关:5244。
endef

define Package/openlist/install
	$(INSTALL_DIR) $(1)/usr/bin $(1)/etc/init.d
	$(INSTALL_BIN) $(PKG_BINDIR)/openlist $(1)/usr/bin/
	$(INSTALL_BIN) ./files/openlist.init $(1)/etc/init.d/openlist
endef

define Build/Compile
endef

$(eval $(call BuildPackage,openlist))
