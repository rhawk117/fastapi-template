#!/usr/bin/env bash


readonly DEST_DIR='keys'
readonly PUBLIC_KEY='jwt_public.pem'
readonly PRIVATE_KEY='jwt_private.pem'

echo "Generating JWT keys in $DEST_DIR..."
openssl genrsa -out "$DEST_DIR/$PRIVATE_KEY" 4096
echo "Private key generated at $DEST_DIR/$PRIVATE_KEY"
openssl rsa -in "$DEST_DIR/$PRIVATE_KEY" -pubout -out "$DEST_DIR/$PUBLIC_KEY"
echo "Public key generated at $DEST_DIR/$PUBLIC_KEY"