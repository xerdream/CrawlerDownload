import execjs


class DecryptM3u8Url():
    def __init__(self):
        self.cwd = r"C:\\Users\\FGx\AppData\\Roaming\\npm\\node_modules"
        self.js_env = execjs.get()

    def __input(self, url: str):
        return url.rsplit("key=")[-1].split('&')[0]

    def __output(self, destr: str):
        return destr.split("|")

    def de2023_6_29(self, url: str, alldata: bool = False):
        enstr = self.__input(url)
        self.js_code = """function unzip(enstr) {
            const CryptoJS = require('crypto-js');
            const key = CryptoJS.enc.Utf8.parse('12348888');
            const iv = CryptoJS.enc.Utf8.parse('');
            const strs = CryptoJS.enc.Hex.parse(enstr);
            const decrypt = CryptoJS.AES.decrypt({'ciphertext': strs},
                        key,
                        {
                        'iv': iv,
                        'mode': CryptoJS.mode.CBC,
                        'padding': CryptoJS.pad.Pkcs7
                        });
                return decrypt.toString(CryptoJS.enc.Utf8).toString();
                }"""

        self.js_compiled = self.js_env.compile(self.js_code, cwd=self.cwd)

        destr = self.js_compiled.eval(f'unzip("{enstr}")')
        return self.__output(destr) if alldata else self.__output(destr)[0]


if __name__ == "__main__":
    url = "http://nos.netease.com/yanxuan/06b01519c11a4c76a67a6aa7c1ed8abc?ID=sina,wx&key=5a857c787dc2d2368854ab082f05691060344e77a3e9d4acec3e02d5ae385ff751944bda94d748cded34a8058b4bf21987ce2f7f41e01bb0c75094e447b78cc97297bb8a92219b0aa0497573f02f9f3e5046436dbd7f8085a18a56136d4ea0cb349d68f47dcb2a2bd2e6673054e66fc29507572948f9dc00dd9b6d8c92a74c7ae67e6bf4a4ce7d173c315abfd3fd74cb5565c41561c32b7ddaba5d3079c31b08871e745dfd83b961b432bff78ad581f73b1a6833a2ee361a494473f1a887fdd0db4834674bf56c6b53a30bd33ea4d503&NB20230717"
    url2 = "http://p3-tt.byteimg.com/obj/tos-cn-i-dcdx/oknYANGxQC4ztIDPHbxfKGGACxdUHg1KAqCAek?G=kuais,Share&key=466280445c3b244a594a6c5099cb94ad298ce03b911a3cd09ddd72024b05ba0f6d88c2fa57591cfe76e99c98752da164a6548072a111d5493ecc43d07738cd3a624dda4932ae1bf8779f4408f702493e9ce08ea0e6076902530c330951508eee1581406fcb9b6484d3bd45086dbe3ad0df4825c5e74951d4ca0b52267b5b2090b251b3b4732d154bf639aacf9c96a2707dda20739453604c42db7374dbc2cacc67da5ca1cb3ad538a117a5242d233598d58ef6c5f61c83932ea1ff42d773f12ec5367422569dd3046030fdfeb7f64840462f2b2719f2eeebb0f96f895436acd6d4074b5add0bc0c4d552cf5543c805c7c5af395871c7b05365137e7e882b54dacf64870478f7211a5eaf5a87cff1fa11&8v20230805"
    url = "b41e9e0db765dcf12ae42a2b131fec66f6882413e5c02efe8a9338fe94c4c307f386ed1d4ea86a1d097f25b5338b5f2c8280005f8eb0253661f1a0f3531b2521971ddca30c82cbb5270a2e8afbf6aaf72630faa148fe3b43f385f40f7ac6a61f8017ffacfe9c83147e51bc0f0dcd7e8146ede75896021abd57fff844ea9ace2d2ca23ff9976a5e6fff5399915f688963e7d836041ce9617dcf7aec6969abe3054998e9fef6b64a8f57fce036169e46b66169beaba5045e81b4412a080b9505bffc8cb7bb87caed08a4a854bab4120406"
    result = DecryptM3u8Url().de2023_6_29(url2)
    print(result)
