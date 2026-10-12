# ddns-go (Go) for loongarch64 — binary repack, see docs/BUILDLOG.md
include $(TOPDIR)/rules.mk

PKG_NAME:=ddns-go
PKG_VERSION:=6.17.7
PKG_RELEASE:=1

PKG_SOURCE:=ddns-go-la-1.tar.gz
PKG_SOURCE_URL:=file:///home/yunix/istore-la-build/local-src/
PKG_HASH:=skip

PKG_BUILD_DIR:=$(BUILD_DIR)/$(PKG_NAME)-$(PKG_VERSION)-la
PKG_BINDIR:=$(BUILD_DIR)

include $(INCLUDE_DIR)/package.mk

define Package/ddns-go
  SECTION:=net
  CATEGORY:=Network
  TITLE:=DDNS client (Go)
  URL:=https://github.com/jeessy2/ddns-go
endef

define Package/ddns-go/description
  ddns-go 龙芯版：宿主 Go GOARCH=loong64 直编，静态链接。
  首次使用：浏览器开 :9876 配 DNS 服务商。
endef

define Package/ddns-go/install
	$(INSTALL_DIR) $(1)/usr/bin $(1)/etc/init.d
	$(INSTALL_BIN) $(PKG_BINDIR)/ddns-go $(1)/usr/bin/
	$(INSTALL_BIN) ./files/ddns-go.init $(1)/etc/init.d/ddns-go
endef

define Build/Compile
endef

$(eval $(call BuildPackage,ddns-go))
