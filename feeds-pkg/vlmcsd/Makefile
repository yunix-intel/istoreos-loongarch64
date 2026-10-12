# vlmcsd (C) for loongarch64 — binary repack (vlmcsd + vlmcs client)
include $(TOPDIR)/rules.mk

PKG_NAME:=vlmcsd
PKG_VERSION:=1.0
PKG_RELEASE:=1

PKG_SOURCE:=vlmcsd-la-1.tar.gz
PKG_SOURCE_URL:=file:///home/yunix/istore-la-build/local-src/
PKG_HASH:=skip

PKG_BUILD_DIR:=$(BUILD_DIR)/$(PKG_NAME)-$(PKG_VERSION)-la
PKG_BINDIR:=$(BUILD_DIR)

include $(INCLUDE_DIR)/package.mk

define Package/vlmcsd
  SECTION:=net
  CATEGORY:=Network
  TITLE:=KMS emulator (C)
endef

define Package/vlmcsd/description
  vlmcsd 龙芯版：交叉工具链编，musl 动态链接。
endef

define Package/vlmcsd/install
	$(INSTALL_DIR) $(1)/usr/bin $(1)/etc/init.d
	$(INSTALL_BIN) $(PKG_BINDIR)/vlmcsd $(1)/usr/bin/
	$(INSTALL_BIN) $(PKG_BINDIR)/vlmcs $(1)/usr/bin/
	$(INSTALL_BIN) ./files/vlmcsd.init $(1)/etc/init.d/vlmcsd
endef

define Build/Compile
endef

$(eval $(call BuildPackage,vlmcsd))
