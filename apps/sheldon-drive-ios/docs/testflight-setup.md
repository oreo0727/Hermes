# TestFlight Setup

This app can be delivered to an iPhone without owning a Mac by using GitHub Actions plus Apple signing.

## Apple Website Steps

1. In Apple Developer, create an explicit App ID:
   - Description: `Sheldon Drive`
   - Bundle ID: `com.oreo0727.hermes.sheldondrive`

2. In App Store Connect, create a new app record:
   - Platform: `iOS`
   - Name: `Sheldon Drive`
   - Bundle ID: `com.oreo0727.hermes.sheldondrive`
   - SKU: `sheldon-drive-ios`
   - User access: `Full Access`

3. Create an App Store Connect API key:
   - App Store Connect > Users and Access > Integrations > App Store Connect API
   - Role: `App Manager`
   - Save the Key ID, Issuer ID, and downloaded `.p8` file.

4. Create an Apple Distribution certificate using a CSR.

5. Create an App Store provisioning profile for `com.oreo0727.hermes.sheldondrive` using that distribution certificate.

6. Add yourself as an internal TestFlight tester after the first build uploads.

## CSR From This Linux Server

Run this once from the repo root:

```bash
mkdir -p private/apple-signing
openssl genrsa -out private/apple-signing/sheldon-drive.key 2048
openssl req -new \
  -key private/apple-signing/sheldon-drive.key \
  -out private/apple-signing/sheldon-drive.csr \
  -subj "/emailAddress=james@james-Openclaw.local,CN=Sheldon Drive Distribution,C=US"
```

Upload `private/apple-signing/sheldon-drive.csr` when Apple asks for the certificate signing request. After Apple gives you a `.cer` file, put it in `private/apple-signing/distribution.cer` and run:

```bash
openssl x509 -inform DER -in private/apple-signing/distribution.cer -out private/apple-signing/distribution.pem
openssl pkcs12 -export \
  -inkey private/apple-signing/sheldon-drive.key \
  -in private/apple-signing/distribution.pem \
  -out private/apple-signing/distribution.p12
```

Choose a strong password for the `.p12`; that password becomes the `APPLE_CERTIFICATE_PASSWORD` GitHub secret.

## GitHub Secrets

Add these in GitHub > Hermes repo > Settings > Secrets and variables > Actions > New repository secret:

- `APPLE_TEAM_ID`
- `APPLE_CERTIFICATE_P12_BASE64`
- `APPLE_CERTIFICATE_PASSWORD`
- `APPLE_KEYCHAIN_PASSWORD`
- `APPLE_PROVISIONING_PROFILE_BASE64`
- `APP_STORE_CONNECT_API_KEY_ID`
- `APP_STORE_CONNECT_API_ISSUER_ID`
- `APP_STORE_CONNECT_API_PRIVATE_KEY`

Create the base64 secret values from the repo root:

```bash
base64 -w 0 private/apple-signing/distribution.p12
base64 -w 0 private/apple-signing/profile.mobileprovision
```

For `APP_STORE_CONNECT_API_PRIVATE_KEY`, paste the full contents of the downloaded `AuthKey_XXXXXXXXXX.p8` file.

## Upload

After the secrets are set, go to GitHub Actions and run:

`Sheldon Drive TestFlight`

When Apple finishes processing the build, open App Store Connect > Sheldon Drive > TestFlight, add yourself as an internal tester, then install Apple's TestFlight app on your iPhone and accept the invite.
