import os
import shutil
import socket
import sys
import thread

#cache variables
CACHE_DIR = 'cachedirectory'
CACHE = {}

#connection variables
MAX_CONN = 50
BUFFER_SIZE = 999999
HOST = ''

def print_to_op(type, request, address):
    if type == "Request":
        colornum = 92
    elif type == "Peer Reset":
        colornum = 93

    print "\033[", colornum, "m", address[0], "\t", type, "\t", request, "\033[0m"

def main():
    # Figure out the port number for the web proxy
    if len(sys.argv) < 2:
        print "Port not specified, using default 8080" 
        port = 8080
    else:
        port = int(sys.argv[1])

    print "Proxy Server Running on %s:%d" % (HOST, port)

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Create a socket
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, port)) # Associate the socket to host and port
        s.listen(MAX_CONN) # Start listening for connections
    except socket.error, (value, message):
        if s:
            s.close()
        print "Could not open socket:", message
        sys.exit(1)

    # Get connections from client
    while 1:
        conn, client_addr = s.accept()
        thread.start_new_thread(proxy_thread, (conn, client_addr)) # Create new thread to handle request

    s.close()



def proxy_thread(conn, client_addr):
    request = conn.recv(BUFFER_SIZE) # Get the request
    print request

    first_line = request.split('\n')[0] # Parse first line
    print first_line

    url = first_line.split(' ')[1] # Get the URL

    print_to_op("Request", first_line, client_addr)
    
    # Find the webserver and port
    http_pos = url.find("://") # Find pos of ://
    if (http_pos==-1):
        temp = url
    else:
        temp = url[(http_pos+3):] # Get the rest of url
    
    port_pos = temp.find(":") # Find the port pos (if any)

    # Find end of web server
    webserver_pos = temp.find("/")
    if webserver_pos == -1:
        webserver_pos = len(temp)

    webserver = ""
    port = -1
    if port_pos==-1 or webserver_pos < port_pos: # Default port
        port = 80
        webserver = temp[:webserver_pos]
    else: # Specific port
        port = int((temp[(port_pos+1):])[:webserver_pos-port_pos-1])
        webserver = temp[:port_pos]

    temp = temp.replace("/", "_")

    if CACHE.has_key(temp):
        print "Fetching the required from cache"
        fp = open(CACHE_DIR + "/" + temp, "r")
        data = fp.read()
        conn.send(data)
        conn.close()
        fp.close()
    else:
        try:
            # Create a socket to connect to the web server
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((webserver, port))
            s.send(request) # Send request to webserver

            save_data = ""
            while 1:
                # Receive data from web server
                data = s.recv(BUFFER_SIZE)
                if len(data) > 0:
                    conn.send(data) # Send data back to the connection
                    save_data += data
                else:
                    break

            fp = open(CACHE_DIR + "/" + temp, "a")
            fp.write(save_data)
            fp.close()
            CACHE[temp] = True
            s.close()
            conn.close()
        except socket.error, (value, message):
            if s:
                s.close()
            if conn:
                conn.close()
            print_to_op("Peer Reset",first_line,client_addr)
            sys.exit(1)

if __name__ == '__main__':
    if os.path.exists(CACHE_DIR):
        shutil.rmtree(CACHE_DIR) #for clearing cache when code is executed newly
    os.makedirs(CACHE_DIR)
    main()
