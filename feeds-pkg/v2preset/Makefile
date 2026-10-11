# v2 preset：首次启动定制（语言 + 服务自启），无密钥内容，可进库
include $(TOPDIR)/rules.mk

PKG_NAME:=v2preset-personal
PKG_VERSION:=1.0
PKG_RELEASE:=1

PKG_BUILD_DIR:=$(BUILD_DIR)/$(PKG_NAME)

include $(INCLUDE_DIR)/package.mk

define Package/v2preset-personal
  SECTION:=base
  CATEGORY:=Base system
  TITLE:=v2 personal first-boot preset (no secrets)
endef

define Package/v2preset-personal/description
  中文默认 + EasyTier/Tailscale/OpenClash 服务自启。
  密钥类文件（network.toml / config.yaml / mihomo 内核）只在构建机本地 files/ 里，
  永不进库。
endef

define Package/v2preset-personal/install
	$(INSTALL_DIR) $(1)/etc/uci-defaults
	$(INSTALL_BIN) ./files/uci-defaults/99-v2-personal $(1)/etc/uci-defaults/
	if [ -d ./files/etc ]; then $(CP) ./files/etc/* $(1)/etc/; fi
endef

define Build/Compile
endef

$(eval $(call BuildPackage,v2preset-personal))
