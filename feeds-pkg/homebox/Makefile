# homebox (Go) for loongarch64 — binary repack
include $(TOPDIR)/rules.mk

PKG_NAME:=homebox
PKG_VERSION:=0.10.3
PKG_RELEASE:=1

PKG_SOURCE:=homebox-la-1.tar.gz
PKG_SOURCE_URL:=file:///home/yunix/istore-la-build/local-src/
PKG_HASH:=skip

PKG_BUILD_DIR:=$(BUILD_DIR)/$(PKG_NAME)-$(PKG_VERSION)-la
PKG_BINDIR:=$(BUILD_DIR)

include $(INCLUDE_DIR)/package.mk

define Package/homebox
  SECTION:=net
  CATEGORY:=Network
  TITLE:=Home inventory (Go)
  URL:=https://github.com/hay-kot/homebox
endef

define Package/homebox/description
  homebox 龙芯版：宿主 Go 直编（含 sqlite 依赖升级，见构建日志）。
  数据目录 /etc/homebox，http://网关:7745。
endef

define Package/homebox/install
	$(INSTALL_DIR) $(1)/usr/bin $(1)/etc/init.d
	$(INSTALL_BIN) $(PKG_BINDIR)/homebox $(1)/usr/bin/
	$(INSTALL_BIN) ./files/homebox.init $(1)/etc/init.d/homebox
endef

define Build/Compile
endef

$(eval $(call BuildPackage,homebox))
