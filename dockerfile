# Start with the Amazon Linux 2 base image to build the layer
FROM amazonlinux:2

# The following is a fix for the CentOS 7 repository being unavailable
# We'll use the vault.centos.org repository instead.
RUN rm -f /etc/yum.repos.d/centos.repo
RUN echo "[centos-vault]" > /etc/yum.repos.d/centos-vault.repo && \
    echo "name=CentOS-7 Vault" >> /etc/yum.repos.d/centos-vault.repo && \
    echo "baseurl=http://vault.centos.org/7.9.2009/os/x86_64/" >> /etc/yum.repos.d/centos-vault.repo && \
    echo "gpgcheck=0" >> /etc/yum.repos.d/centos-vault.repo && \
    echo "enabled=1" >> /etc/yum.repos.d/centos-vault.repo

# Install necessary dependencies, including zip for packaging the layer
RUN yum clean all && \
    yum update -y && \
    yum install -y \
        gcc \
        gcc-c++ \
        make \
        wget \
        bzip2 \
        libXrender \
        cups-libs \
        libXext \
        libXrandr \
        libXt \
        libXtst \
        libXv \
        libXxf86vm \
        libXinerama \
        libXft \
        liblangtag \
        pango \
        cairo \
        fontconfig \
        mesa-libGLU \
        liberation-fonts \
        dejavu-sans-fonts \
        dejavu-serif-fonts \
        ghostscript \
        zip

# Download and install a newer, stable version of LibreOffice from a direct link
RUN wget https://downloadarchive.documentfoundation.org/libreoffice/old/7.6.7.2/rpm/x86_64/LibreOffice_7.6.7.2_Linux_x86-64_rpm.tar.gz -O /tmp/libreoffice.tar.gz
RUN tar -xzf /tmp/libreoffice.tar.gz -C /opt
RUN rpm -Uvh /opt/LibreOffice_7.6.7.2_Linux_x86-64_rpm/RPMS/*.rpm --nodeps

# Set up the environment for the Lambda layer
ENV PATH=/opt/libreoffice7.6/program:$PATH

# Create a directory to hold the final zipped layer
RUN mkdir -p /layer/
RUN mv /opt/libreoffice7.6 /layer/

# Clean up
RUN rm -rf /opt/LibreOffice_7.6.7.2_Linux_x86-64_rpm /tmp/libreoffice.tar.gz

# The CMD is changed to execute the build script
CMD ["/build-libreoffice-layer.sh"]
