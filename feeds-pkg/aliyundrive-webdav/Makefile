# aliyundrive-webdav (Rust, ring>=0.17 surgery) for loongarch64
include $(TOPDIR)/rules.mk

PKG_NAME:=aliyundrive-webdav
PKG_VERSION:=2.3.3
PKG_RELEASE:=1

PKG_SOURCE:=aliyundrive-la-1.tar.gz
PKG_SOURCE_URL:=file:///home/yunix/istore-la-build/local-src/
PKG_HASH:=skip

PKG_BUILD_DIR:=$(BUILD_DIR)/$(PKG_NAME)-$(PKG_VERSION)-la
PKG_BINDIR:=$(BUILD_DIR)

include $(INCLUDE_DIR)/package.mk

define Package/aliyundrive-webdav
  SECTION:=net
  CATEGORY:=Network
  TITLE:=AliyunDrive WebDAV (Rust)
  URL:=https://github.com/messense/aliyundrive-webdav
endef

define Package/aliyundrive-webdav/description
  aliyundrive-webdav 龙芯版：ring 0.16→0.17 手术链（rustls/reqwest/tokio-rustls
  同步升级）后编出，musl 动态链接。扫码登录配 refresh-token 后启动。
endef

define Package/aliyundrive-webdav/install
	$(INSTALL_DIR) $(1)/usr/bin $(1)/etc/init.d
	$(INSTALL_BIN) $(PKG_BINDIR)/aliyundrive $(1)/usr/bin/
	$(INSTALL_BIN) ./files/aliyundrive.init $(1)/etc/init.d/aliyundrive
endef

define Build/Compile
endef

$(eval $(call BuildPackage,aliyundrive-webdav))
