#!/usr/bin/env python
"""
Generate self-signed SSL certificates for local development.
This creates cert.pem and key.pem files for HTTPS support.
"""
import os
import sys
from datetime import datetime, timedelta

# Check Python version
if sys.version_info < (3, 7):
    print("Error: Python 3.7 or higher is required.")
    sys.exit(1)

# Try importing cryptography with better error handling
try:
    from cryptography import x509
    from cryptography.x509.oid import NameOID
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.backends import default_backend
except ImportError as e:
    print("=" * 60)
    print("ERROR: Required cryptography module not found!")
    print("=" * 60)
    print(f"\nImport error details: {e}")
    print("\nPLEASE FOLLOW THESE STEPS:")
    print("1. Make sure your virtual environment is activated")
    print("   Windows: .\\env\\Scripts\\Activate.ps1")
    print("   Linux/Mac: source env/bin/activate")
    print("\n2. Install cryptography:")
    print("   pip install cryptography")
    print("\n3. If it's already installed, try reinstalling:")
    print("   pip uninstall cryptography -y")
    print("   pip install cryptography")
    print("\n4. Verify installation:")
    print('   python -c "import cryptography; print(cryptography.__version__)"')
    print("=" * 60)
    sys.exit(1)


def generate_certificate_files(output_dir="."):
    """
    Generate self-signed SSL certificate and private key.
    
    Args:
        output_dir: Directory where cert.pem and key.pem will be created
    """
    # Ensure output directory exists
    if not os.path.exists(output_dir):
        print(f"Creating directory: {output_dir}")
        try:
            os.makedirs(output_dir)
        except Exception as e:
            print(f"Error creating directory: {e}")
            sys.exit(1)
    
    print("\n" + "=" * 60)
    print("Generating Self-Signed SSL Certificate")
    print("=" * 60)
    print(f"Output directory: {os.path.abspath(output_dir)}\n")
    
    try:
        # Generate private key
        print("1. Generating RSA private key (2048 bits)...")
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        print("   ✓ Private key generated")
        
        # Create certificate subject and issuer
        print("\n2. Creating certificate attributes...")
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "State"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "City"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Connectly Development"),
            x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
        ])
        print("   ✓ Certificate attributes created")
        
        # Build certificate
        print("\n3. Building certificate...")
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.utcnow()
        ).not_valid_after(
            datetime.utcnow() + timedelta(days=365)
        ).add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName("localhost"),
                x509.DNSName("127.0.0.1"),
                x509.IPAddress(__import__('ipaddress').IPv4Address("127.0.0.1")),
            ]),
            critical=False,
        ).sign(private_key, hashes.SHA256(), default_backend())
        print("   ✓ Certificate built and signed")
        
        # Write private key file
        print("\n4. Writing private key to file...")
        key_path = os.path.join(output_dir, "key.pem")
        with open(key_path, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            ))
        print(f"   ✓ Private key: {os.path.abspath(key_path)}")
        
        # Write certificate file
        print("\n5. Writing certificate to file...")
        cert_path = os.path.join(output_dir, "cert.pem")
        with open(cert_path, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        print(f"   ✓ Certificate: {os.path.abspath(cert_path)}")
        
        print("\n" + "=" * 60)
        print("SUCCESS! SSL certificates generated")
        print("=" * 60)
        print("\nCertificate Details:")
        print(f"  - Valid for: 365 days")
        print(f"  - Common Name: localhost")
        print(f"  - Subject Alternative Names: localhost, 127.0.0.1")
        
        return cert_path, key_path
        
    except Exception as e:
        print(f"\n✗ Error generating certificates: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    """Main function to generate certificates."""
    print("\nConnectly API - SSL Certificate Generator")
    
    # Get script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Generate certificates in project root (for use with ../cert.pem)
    print("\n[Generating certificates in project root]")
    root_cert, root_key = generate_certificate_files(script_dir)
    
    # Also generate in connectly_project directory for convenience
    connectly_dir = os.path.join(script_dir, "connectly_project")
    if os.path.exists(connectly_dir):
        print("\n[Copying certificates to connectly_project directory]")
        try:
            import shutil
            shutil.copy2(root_cert, os.path.join(connectly_dir, "cert.pem"))
            shutil.copy2(root_key, os.path.join(connectly_dir, "key.pem"))
            print("   ✓ Certificates copied to connectly_project/")
        except Exception as e:
            print(f"   ! Could not copy to connectly_project: {e}")
    
    print("\n" + "=" * 60)
    print("NEXT STEPS:")
    print("=" * 60)
    print("\n1. Navigate to the connectly_project directory:")
    print("   cd connectly_project")
    print("\n2. Run the HTTPS development server:")
    print("   python manage.py runserver_plus --cert-file ../cert.pem --key-file ../key.pem")
    print("\n   OR (if you copied files to connectly_project):")
    print("   python manage.py runserver_plus --cert-file cert.pem --key-file key.pem")
    print("\n3. Access the API at:")
    print("   https://127.0.0.1:8000/api/")
    print("\n4. Your browser will show a security warning (this is normal")
    print("   for self-signed certificates). Click 'Advanced' and proceed.")
    print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
