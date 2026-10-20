# sunpanel (Go) for loongarch64 — binary repack (+web/ frontend at runtime)
include $(TOPDIR)/rules.mk

PKG_NAME:=sunpanel
PKG_VERSION:=1.8.1
PKG_RELEASE:=1

PKG_SOURCE:=sunpanel-la-1.tar.gz
PKG_SOURCE_URL:=file:///home/yunix/istore-la-build/local-src/
PKG_HASH:=skip

PKG_BUILD_DIR:=$(BUILD_DIR)/$(PKG_NAME)-$(PKG_VERSION)-la
PKG_BINDIR:=$(BUILD_DIR)

include $(INCLUDE_DIR)/package.mk

define Package/sunpanel
  SECTION:=net
  CATEGORY:=Network
  TITLE:=Nav panel (Go)
endef

define Package/sunpanel/description
  sunpanel 龙芯版：宿主 Go 直编（含 sqlite 升级）。注意：运行时另需前端 web/ 目录，
  见构建记录；配好后 http://网关:8080。
endef

define Package/sunpanel/install
	$(INSTALL_DIR) $(1)/usr/bin $(1)/etc/init.d
	$(INSTALL_BIN) $(PKG_BINDIR)/sunpanel $(1)/usr/bin/
	$(INSTALL_BIN) ./files/sunpanel.init $(1)/etc/init.d/sunpanel
endef

define Build/Compile
endef

$(eval $(call BuildPackage,sunpanel))
