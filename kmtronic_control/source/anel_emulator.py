import uvicorn
from fastapi import FastAPI, Request
from relay import KMTronicBreaker
import sys

args = sys.argv
print("KMTronic_IP = " + str(args[1]))
print("ANEL_IP = " + str(args[2]))
print("PORT = " + str(args[3]))

KMTronic_IP = str(args[1])
ANEL_IP = str(args[2])
PORT = int(args[3])

app = FastAPI()


@app.get("/strg.cfg")
async def read():
    relay = KMTronicBreaker(KMTronic_IP)
    state = relay.state()
    statestring = ""
    for x in state:
        statestring = statestring + str(x) + ";"
    return "NET-PWRCTRL_04.5;NET-CONTROL    ;"+ANEL_IP+";255.255.255.0;192.168.0.1;00:04:A3:12:04:89;"+str(PORT)+";25.4;P;;Nr. "\
           "1;Nr. 2;Nr. 3;Nr. 4;Nr. 5;Nr. 6;Nr. 7;Nr. 8;;;"+statestring+";;0;0;0;0;0;0;0;0;;;aus vom " \
           "Browser;Anfangsstatus;Anfangsstatus;Anfangsstatus;Anfangsstatus;Anfangsstatus;Anfangsstatus;Anfangsstatus" \
           ";;;;;;;;;;;end;NET - Power Control"


@app.post("/ctrl.htm")
async def load(request: Request):
    relay = KMTronicBreaker(KMTronic_IP)
    data = await request.body()
    data_decode = data.decode()
    print(int(data_decode[1]))
    relay.set_channel_states(int(data_decode[1])+1)
    return str(data.decode())


if __name__ == "__main__":
    uvicorn.run(app, host=ANEL_IP, port=PORT)


