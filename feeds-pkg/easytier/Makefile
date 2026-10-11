# EasyTier mesh VPN (binary repack for loongarch64)
# 上游官方 loongarch64 二进制直装包，无需编译。
include $(TOPDIR)/rules.mk

PKG_NAME:=easytier
PKG_VERSION:=2.6.4
PKG_RELEASE:=1

PKG_SOURCE:=easytier-linux-loongarch64-v$(PKG_VERSION).zip
PKG_SOURCE_URL:=https://github.com/EasyTier/EasyTier/releases/download/v$(PKG_VERSION)/
PKG_HASH:=skip

PKG_BUILD_DIR:=$(BUILD_DIR)/$(PKG_NAME)-$(PKG_VERSION)
PKG_BINDIR:=$(PKG_BUILD_DIR)/easytier-linux-loongarch64

include $(INCLUDE_DIR)/package.mk

define Package/easytier
  SECTION:=net
  CATEGORY:=Network
  TITLE:=EasyTier decentralized mesh VPN
  URL:=https://github.com/EasyTier/EasyTier
  DEPENDS:=+kmod-tun
endef

define Package/easytier/description
  EasyTier 龙芯版直装包：官方 loongarch64 二进制 + init.d 自启。
  配置见 /etc/easytier/easytier.conf（EXTRA_ARGS 透传，填 easytier-core 参数）。
endef

# 二进制直装包，无需编译（空 recipe 覆盖默认的 make 调用，否则会因包内无 Makefile 而失败）
define Build/Compile
endef

define Package/easytier/install
	$(INSTALL_DIR) $(1)/usr/bin $(1)/etc/init.d $(1)/etc/easytier
	$(INSTALL_BIN) $(PKG_BINDIR)/easytier-core $(1)/usr/bin/
	$(INSTALL_BIN) $(PKG_BINDIR)/easytier-cli $(1)/usr/bin/
	$(INSTALL_BIN) ./files/easytier.init $(1)/etc/init.d/easytier
	$(INSTALL_CONF) ./files/easytier.conf $(1)/etc/easytier/easytier.conf
endef

$(eval $(call BuildPackage,easytier))
