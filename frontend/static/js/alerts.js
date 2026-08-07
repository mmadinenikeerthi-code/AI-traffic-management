async function checkAlerts() {

    const token =
        localStorage.getItem("access_token") ||
        localStorage.getItem("token");

    try{

        const response = await fetch("/alerts",{
            headers:{
                Authorization:`Bearer ${token}`
            }
        });

        if(!response.ok) return;

        const alerts = await response.json();

        alerts.forEach(alert=>{

            if(Notification.permission==="granted"){

                new Notification("🚨 Traffic Alert",{

                    body: alert.message,
                    icon:"/static/images/logo.png"

                });

            }

        });

    }
    catch(err){
        console.log(err);
    }

}

if(Notification.permission!=="granted"){
    Notification.requestPermission();
}

setInterval(checkAlerts,5000);