# Use the official Nginx Alpine image
FROM nginx:alpine

LABEL org.opencontainers.image.source="https://github.com/mrgionsi/remote-checkin"

# Create a non-root user and group

# Copy the custom Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy Angular build output
COPY dist/remote-checkin/browser /usr/share/nginx/html



# Expose the default HTTP port
EXPOSE 80

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]
