<%@ WebHandler Language="C#" Class="XtreeData2" %>

using System.Text;
using System.Web;

public class XtreeData2 : IHttpHandler
{

    public void ProcessRequest(HttpContext context)
    {
        StringBuilder str = new StringBuilder();

        str.Append("[");
        str.Append("{title:\"节点1\",value:\"jd1\",data:[");
        str.Append("{title:\"节点1.1\",value:\"jd1.1\",data:[]}");
        str.Append(",{title:\"节点1.2\",value:\"jd1.2\",data:[]}");
        str.Append(",{title:\"节点1.3\",value:\"jd1.3\",data:[]}");
        str.Append(",{title:\"节点1.4\",value:\"jd1.4\",data:[]}");
        str.Append("]}");
        str.Append(",{title:\"节点2\",value:\"jd2\",data:[");
        str.Append("{title:\"节点2.1\",value:\"jd2.1\",data:[]}");
        str.Append(",{title:\"节点2.2\",value:\"jd2.2\",data:[");
        str.Append("{title:\"节点2.2.1\",value:\"jd2.2.1\",data:[]}");
        str.Append(",{title:\"节点2.2.2\",value:\"jd2.2.2\",data:[]}");
        str.Append(",{title:\"节点2.2.3\",value:\"jd2.2.3\",data:[]}");
        str.Append(",{title:\"节点2.2.4\",value:\"jd2.2.4\",data:[]}]}");
        str.Append(",{title:\"节点2.3\",value:\"jd2.3\",data:[]}");
        str.Append(",{title:\"节点2.4\",value:\"jd2.4\",data:[]}");
        str.Append("]}");
        str.Append("]");

        context.Response.Write(str);
        context.Response.End();
    }

    public bool IsReusable
    {
        get
        {
            return false;
        }
    }

}